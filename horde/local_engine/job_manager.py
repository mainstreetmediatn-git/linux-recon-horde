import json
import os
import signal
import subprocess
import threading
import uuid
from concurrent.futures import Future, ThreadPoolExecutor
from datetime import datetime, timezone
from pathlib import Path
from typing import Any, Dict, Optional

from horde.local_engine.execution_engine import ExecutionEngine
from horde.local_engine.models import ModuleDefinition


class JobManager:
    TERMINAL_STATES = {
        "completed",
        "failed",
        "cancelled",
        "timed_out",
        "interrupted",
    }

    def __init__(self, logs_dir: Path, max_workers: int = 4):
        self.logs_dir = logs_dir
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.job_dirs: Dict[str, Path] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.futures: Dict[str, Future] = {}
        self.shutting_down = False
        self.lock = threading.Lock()
        self.worker_pool = ThreadPoolExecutor(
            max_workers=max_workers,
            thread_name_prefix="horde-worker",
        )
        self.logs_dir.mkdir(parents=True, exist_ok=True)

    def _create_job_dir(self, job_id: str) -> Path:
        now = datetime.now(timezone.utc)
        path = (
            self.logs_dir
            / now.strftime("%Y")
            / now.strftime("%m")
            / now.strftime("%d")
            / job_id
        )
        path.mkdir(parents=True, exist_ok=True)
        return path

    def _persist_job(self, job_id: str, data: dict) -> None:
        job_dir = self.job_dirs.get(job_id)
        if not job_dir:
            job_dir = self._create_job_dir(job_id)
            self.job_dirs[job_id] = job_dir

        target_file = job_dir / "job.json"
        tmp_file = job_dir / "job.json.tmp"

        with open(tmp_file, "w", encoding="utf-8") as handle:
            json.dump(data, handle, indent=4)
            handle.flush()
            os.fsync(handle.fileno())

        os.replace(tmp_file, target_file)

    def _terminate_process_group(self, process: subprocess.Popen) -> None:
        if process.poll() is not None:
            return
        try:
            os.killpg(os.getpgid(process.pid), signal.SIGTERM)
        except ProcessLookupError:
            return
        except Exception:
            try:
                process.terminate()
            except Exception:
                pass

    def _stop_process_group(
        self,
        process: subprocess.Popen,
        grace_seconds: float = 5.0,
    ) -> None:
        if process.poll() is not None:
            return

        self._terminate_process_group(process)
        try:
            process.wait(timeout=grace_seconds)
            return
        except subprocess.TimeoutExpired:
            pass

        try:
            os.killpg(os.getpgid(process.pid), signal.SIGKILL)
        except ProcessLookupError:
            return
        except Exception:
            try:
                process.kill()
            except Exception:
                pass

        try:
            process.wait(timeout=2.0)
        except Exception:
            pass

    def recover(self) -> None:
        if not self.logs_dir.exists():
            return

        for json_file in self.logs_dir.glob("**/job.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as handle:
                    data = json.load(handle)

                job_id = data.get("job_id")
                if not job_id:
                    continue

                self.job_dirs[job_id] = json_file.parent

                if data.get("status") in {"queued", "running", "cancelling"}:
                    data["status"] = "interrupted"
                    data["error"] = "Server restarted while job was active."
                    data["finished_at"] = datetime.now(timezone.utc).isoformat()
                    self._persist_job(job_id, data)

                with self.lock:
                    self.jobs[job_id] = data
            except Exception:
                continue

    def shutdown(self) -> None:
        with self.lock:
            self.shutting_down = True
            processes = list(self.processes.values())
            now_iso = datetime.now(timezone.utc).isoformat()

            for job_id, job in self.jobs.items():
                if job["status"] == "queued":
                    job["status"] = "interrupted"
                    job["finished_at"] = now_iso
                    job["error"] = "Server shut down before job execution."
                    self._persist_job(job_id, job)
                elif job["status"] == "running":
                    job["status"] = "cancelling"
                    job["error"] = "Server shutdown requested while job was active."
                    self._persist_job(job_id, job)

        for process in processes:
            self._stop_process_group(process, grace_seconds=5.0)

        self.worker_pool.shutdown(wait=True, cancel_futures=True)

        with self.lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            for job_id, job in self.jobs.items():
                if job["status"] in {"running", "cancelling"}:
                    job["status"] = "interrupted"
                    job["finished_at"] = now_iso
                    job["error"] = "Server shutdown interrupted active job."
                    self._persist_job(job_id, job)

    def _remove_future(self, job_id: str) -> None:
        with self.lock:
            self.futures.pop(job_id, None)

    def create_job(
        self,
        module: ModuleDefinition,
        target: str,
        mode: str = "automatic",
        manual_instructions: Optional[dict] = None,
    ) -> str:
        job_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        is_manual = mode == "manual_fallback"

        job_data: Dict[str, Any] = {
            "job_id": job_id,
            "module_id": module.module_id,
            "status": "completed" if is_manual else "queued",
            "mode": mode,
            "created_at": now_iso,
            "started_at": now_iso if is_manual else None,
            "finished_at": now_iso if is_manual else None,
            "target": target,
            "exit_code": 0 if is_manual else None,
            "error": None,
        }
        if manual_instructions:
            job_data["instructions"] = manual_instructions

        future: Optional[Future] = None

        with self.lock:
            if self.shutting_down:
                raise RuntimeError(
                    "Server is shutting down. Cannot accept new jobs."
                )

            job_dir = self._create_job_dir(job_id)
            self.job_dirs[job_id] = job_dir
            self.jobs[job_id] = job_data
            self._persist_job(job_id, job_data)

            if not is_manual:
                try:
                    future = self.worker_pool.submit(
                        self._run_job_task,
                        job_id,
                        module,
                        target,
                    )
                except RuntimeError:
                    job_data["status"] = "interrupted"
                    job_data["finished_at"] = datetime.now(
                        timezone.utc
                    ).isoformat()
                    job_data["error"] = (
                        "Job submission interrupted during server shutdown."
                    )
                    self._persist_job(job_id, job_data)
                    raise

                self.futures[job_id] = future

        if future is not None:
            future.add_done_callback(lambda _: self._remove_future(job_id))

        return job_id

    def _run_job_task(
        self,
        job_id: str,
        module: ModuleDefinition,
        target: str,
    ) -> None:
        with self.lock:
            job = self.jobs.get(job_id)
            if not job or job["status"] != "queued":
                return

            job["status"] = "running"
            job["started_at"] = datetime.now(timezone.utc).isoformat()
            self._persist_job(job_id, job)

        job_dir = self.job_dirs[job_id]
        stdout_path = job_dir / "stdout.log"
        stderr_path = job_dir / "stderr.log"

        try:
            _, process = ExecutionEngine.run_process(
                module.execution.executable,
                module.execution.args,
                target,
                stdout_path,
                stderr_path,
            )

            with self.lock:
                self.processes[job_id] = process
                job = self.jobs.get(job_id)
                should_stop = (
                    self.shutting_down
                    or not job
                    or job["status"] in {"cancelling", "cancelled"}
                )

            if should_stop:
                self._stop_process_group(process, grace_seconds=2.0)

            timeout_sec = module.execution.timeout_seconds
            try:
                exit_code = process.wait(timeout=timeout_sec)
            except subprocess.TimeoutExpired:
                self._stop_process_group(process, grace_seconds=5.0)
                exit_code = process.wait()

                with self.lock:
                    self.processes.pop(job_id, None)
                    job = self.jobs.get(job_id)
                    if job:
                        if self.shutting_down:
                            job["status"] = "interrupted"
                            job["error"] = (
                                "Server shutdown interrupted active job."
                            )
                        elif job["status"] in {"cancelling", "cancelled"}:
                            job["status"] = "cancelled"
                        else:
                            job["status"] = "timed_out"
                        job["finished_at"] = datetime.now(
                            timezone.utc
                        ).isoformat()
                        job["exit_code"] = exit_code
                        self._persist_job(job_id, job)
                return

            with self.lock:
                self.processes.pop(job_id, None)
                job = self.jobs.get(job_id)
                if not job:
                    return

                if self.shutting_down:
                    job["status"] = "interrupted"
                    job["error"] = "Server shutdown interrupted active job."
                elif job["status"] in {"cancelling", "cancelled"}:
                    job["status"] = "cancelled"
                else:
                    job["status"] = "completed" if exit_code == 0 else "failed"

                job["finished_at"] = datetime.now(timezone.utc).isoformat()
                job["exit_code"] = exit_code
                self._persist_job(job_id, job)

        except Exception as exc:
            with self.lock:
                self.processes.pop(job_id, None)
                job = self.jobs.get(job_id)
                if not job:
                    return

                if self.shutting_down:
                    job["status"] = "interrupted"
                    job["error"] = "Server shutdown interrupted active job."
                elif job["status"] in {"cancelling", "cancelled"}:
                    job["status"] = "cancelled"
                else:
                    job["status"] = "failed"
                    job["error"] = str(exc)

                job["finished_at"] = datetime.now(timezone.utc).isoformat()
                job["exit_code"] = -1
                self._persist_job(job_id, job)

    def cancel_job(self, job_id: str) -> bool:
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return False

            status = job["status"]
            if status in self.TERMINAL_STATES:
                return False

            if status == "queued":
                future = self.futures.get(job_id)
                if future:
                    future.cancel()
                job["status"] = "cancelled"
                job["finished_at"] = datetime.now(timezone.utc).isoformat()
                self._persist_job(job_id, job)
                return True

            if status == "running":
                job["status"] = "cancelling"
                self._persist_job(job_id, job)
                process = self.processes.get(job_id)
            else:
                return False

        if process:
            self._stop_process_group(process, grace_seconds=2.0)

        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return False
            job["status"] = "cancelled"
            job["finished_at"] = datetime.now(timezone.utc).isoformat()
            self._persist_job(job_id, job)
            return True

    def get_job_dir(self, job_id: str) -> Optional[Path]:
        with self.lock:
            path = self.job_dirs.get(job_id)
        if path:
            return path

        matches = list(self.logs_dir.glob(f"**/{job_id}/job.json"))
        if not matches:
            return None

        job_dir = matches[0].parent
        with self.lock:
            self.job_dirs[job_id] = job_dir
        return job_dir
