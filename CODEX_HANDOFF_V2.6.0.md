# Linux Recon Horde — Codex Handoff — v2.6.0 FINAL

## Mission

Continue the existing `mainstreetmediatn-git/linux-recon-horde` codebase from the locked backend implementation below. **Do not redesign or regenerate the architecture.** Use this document as the canonical source of truth for the local-first execution engine unless an actual failing test proves a narrowly scoped correction is necessary.

The architecture is frozen. The task now is to install/align these exact files in the working tree, create the destructive/integration pytest harness, run it, diagnose failures, patch only proven defects, rerun, and produce release evidence.

## Non-negotiable rules

1. Preserve the component boundaries and API contracts below.
2. Do not replace `Popen` execution with shell strings or `shell=True`.
3. Do not remove process-group/session isolation.
4. Do not weaken target validation, risk acknowledgement, durability, recovery, timeout, cancellation, or shutdown semantics.
5. Do not rewrite working components merely for style.
6. Any source change after this handoff must be justified by a reproducible failing test.
7. Do not push to `main`, merge, tag, or publish without explicit approval.
8. Keep test subprocesses harmless and disposable; never target external systems.
9. Show every file created/modified, important diffs, exact test commands/results, discovered bugs, and final git status.
10. Completion signal requires all release gates at the end of this document.

---

# Locked source code

## `horde/models.py`

```python
from pydantic import BaseModel, Field
from typing import List, Optional, Literal, Dict, Any

TargetType = Literal[
    "hostname",
    "domain",
    "ipv4",
    "ipv6",
    "ip",
    "cidr",
    "url",
]

class ExecutionDefinition(BaseModel):
    executable: str
    args: List[str]
    timeout_seconds: int = Field(default=300, ge=1, le=86400)
    ai_agent_command: Optional[str] = None
    manual_runbook: Optional[Dict[str, Any]] = None

class ModuleDefinition(BaseModel):
    module_id: str
    name: str
    category: str = "Uncategorized"
    risk_level: Literal["Low", "Medium", "High", "Critical"]
    target_type: TargetType
    description: str = ""
    potential_consequences: List[str] = Field(default_factory=list)
    system_impact: str = ""
    execution: ExecutionDefinition

class ExecutionRequest(BaseModel):
    module_id: str
    target: str
    force_manual: bool = False
    user_acknowledged: bool = False
```

## `horde/target_validator.py`

```python
import ipaddress
import re
from urllib.parse import urlparse

class TargetValidator:
    HOSTNAME_REGEX = re.compile(r"^(?=.{1,253}$)(?!-)[A-Za-z0-9-]{1,63}(?<!-)(\.[A-Za-z0-9-]{1,63})*$")
    DOMAIN_REGEX = re.compile(r"^(?=.{1,253}$)(?:(?!-)[A-Za-z0-9-]{1,63}(?<!-)\.)+[A-Za-z]{2,63}$")

    @staticmethod
    def validate(target: str, target_type: str) -> str:
        if not isinstance(target, str) or not target.strip():
            raise ValueError("Target must be a non-empty string.")

        target = target.strip()

        if target_type == "ipv4":
            try:
                addr = ipaddress.ip_address(target)
                if addr.version != 4:
                    raise ValueError("Target is not a valid IPv4 address.")
            except ValueError as e:
                raise ValueError(f"Invalid IPv4 address format: {e}")

        elif target_type == "ipv6":
            try:
                addr = ipaddress.ip_address(target)
                if addr.version != 6:
                    raise ValueError("Target is not a valid IPv6 address.")
            except ValueError as e:
                raise ValueError(f"Invalid IPv6 address format: {e}")

        elif target_type == "ip":
            try:
                ipaddress.ip_address(target)
            except ValueError as e:
                raise ValueError(f"Invalid IP address format: {e}")

        elif target_type == "cidr":
            try:
                ipaddress.ip_network(target, strict=False)
            except ValueError as e:
                raise ValueError(f"Invalid CIDR notation format: {e}")

        elif target_type == "hostname":
            if not TargetValidator.HOSTNAME_REGEX.match(target):
                raise ValueError("Invalid hostname format.")

        elif target_type == "domain":
            if not TargetValidator.DOMAIN_REGEX.match(target):
                raise ValueError("Invalid domain format.")

        elif target_type == "url":
            parsed = urlparse(target)
            if parsed.scheme not in ("http", "https") or not parsed.netloc:
                raise ValueError("Invalid URL format. Must include http/https scheme and netloc.")

        else:
            raise ValueError(f"Unsupported target_type: {target_type}")

        return target
```

## `horde/module_registry.py`

```python
import os
import json
import glob
from pathlib import Path
from typing import Dict, List, Optional, Any
from horde.models import ModuleDefinition

class ModuleRegistry:
    def __init__(self, modules_dir: Path):
        self.modules_dir = modules_dir
        self._cache: Dict[str, ModuleDefinition] = {}
        self._errors: List[Dict[str, str]] = []
        self.refresh()

    def refresh(self):
        self._cache.clear()
        self._errors.clear()

        module_files = glob.glob(str(self.modules_dir / "**/*.json"), recursive=True)
        seen_ids = set()

        for file_path in module_files:
            rel_path = os.path.relpath(file_path, self.modules_dir)
            try:
                with open(file_path, 'r', encoding='utf-8') as f:
                    raw_data = json.load(f)

                module = ModuleDefinition.model_validate(raw_data)

                if module.module_id in seen_ids:
                    self._errors.append({
                        "file": rel_path,
                        "error": f"Duplicate module_id detected: '{module.module_id}'"
                    })
                    continue

                seen_ids.add(module.module_id)
                self._cache[module.module_id] = module

            except json.JSONDecodeError as je:
                self._errors.append({"file": rel_path, "error": f"Invalid JSON: {str(je)}"})
            except Exception as ex:
                self._errors.append({"file": rel_path, "error": str(ex)})

    def get_module(self, module_id: str) -> Optional[ModuleDefinition]:
        return self._cache.get(module_id)

    def list_modules(self) -> List[Dict[str, Any]]:
        return [m.model_dump() for m in self._cache.values()]

    def list_errors(self) -> List[Dict[str, str]]:
        return self._errors
```

## `horde/policy.py`

```python
class PolicyEngine:
    @staticmethod
    def validate_execution_policy(risk_level: str, user_acknowledged: bool) -> tuple[bool, str]:
        if risk_level in ["High", "Critical"] and not user_acknowledged:
            return False, f"Module is rated {risk_level} risk. Explicit user acknowledgement is required."
        return True, "Passed policy check."
```

## `horde/execution_engine.py`

```python
import subprocess
from pathlib import Path
from typing import Tuple

class ExecutionEngine:
    @staticmethod
    def run_process(executable: str, args: list[str], target: str, stdout_path: Path, stderr_path: Path) -> Tuple[int, subprocess.Popen]:
        formatted_args = [arg.format(target=target) for arg in args]
        cmd_array = [executable] + formatted_args

        stdout_file = open(stdout_path, "w", encoding="utf-8")
        stderr_file = open(stderr_path, "w", encoding="utf-8")
        try:
            process = subprocess.Popen(
                cmd_array,
                stdout=stdout_file,
                stderr=stderr_file,
                text=True,
                shell=False,
                start_new_session=True
            )
        finally:
            stdout_file.close()
            stderr_file.close()

        return process.pid, process
```

## `horde/job_manager.py`

This version includes the final atomic create-vs-shutdown boundary and shutdown state normalization agreed after rc2.

```python
import uuid
import json
import os
import signal
import threading
import subprocess
from pathlib import Path
from datetime import datetime, timezone
from concurrent.futures import ThreadPoolExecutor, Future
from typing import Dict, Any, Optional
from horde.models import ModuleDefinition
from horde.execution_engine import ExecutionEngine

class JobManager:
    def __init__(self, logs_dir: Path, max_workers: int = 4):
        self.logs_dir = logs_dir
        self.jobs: Dict[str, Dict[str, Any]] = {}
        self.job_dirs: Dict[str, Path] = {}
        self.processes: Dict[str, subprocess.Popen] = {}
        self.futures: Dict[str, Future] = {}
        self.shutting_down = False
        self.lock = threading.Lock()
        self.worker_pool = ThreadPoolExecutor(max_workers=max_workers, thread_name_prefix="horde-worker")
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

    def _persist_job(self, job_id: str, data: dict):
        job_dir = self.job_dirs.get(job_id)
        if not job_dir:
            job_dir = self._create_job_dir(job_id)
            self.job_dirs[job_id] = job_dir

        target_file = job_dir / "job.json"
        tmp_file = job_dir / "job.json.tmp"

        with open(tmp_file, "w", encoding="utf-8") as f:
            json.dump(data, f, indent=4)
            f.flush()
            os.fsync(f.fileno())

        os.replace(tmp_file, target_file)

    def _terminate_process_group(self, process: subprocess.Popen):
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

    def _stop_process_group(self, process: subprocess.Popen, grace_seconds: float = 5.0):
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

    def recover(self):
        if not self.logs_dir.exists():
            return

        for json_file in self.logs_dir.glob("**/job.json"):
            try:
                with open(json_file, "r", encoding="utf-8") as f:
                    data = json.load(f)

                job_id = data.get("job_id")
                if not job_id:
                    continue

                self.job_dirs[job_id] = json_file.parent

                if data.get("status") in ["queued", "running", "cancelling"]:
                    data["status"] = "interrupted"
                    data["error"] = "Server restarted while job was active."
                    data["finished_at"] = datetime.now(timezone.utc).isoformat()
                    self._persist_job(job_id, data)

                with self.lock:
                    self.jobs[job_id] = data
            except Exception:
                continue

    def shutdown(self):
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

        for proc in processes:
            self._stop_process_group(proc, grace_seconds=5.0)

        self.worker_pool.shutdown(wait=True, cancel_futures=True)

        with self.lock:
            now_iso = datetime.now(timezone.utc).isoformat()
            for job_id, job in self.jobs.items():
                if job["status"] in {"running", "cancelling"}:
                    job["status"] = "interrupted"
                    job["finished_at"] = now_iso
                    job["error"] = "Server shutdown interrupted active job."
                    self._persist_job(job_id, job)

    def _remove_future(self, job_id: str):
        with self.lock:
            self.futures.pop(job_id, None)

    def create_job(self, module: ModuleDefinition, target: str, mode: str = "automatic", manual_instructions: Optional[dict] = None) -> str:
        job_id = str(uuid.uuid4())
        now_iso = datetime.now(timezone.utc).isoformat()
        is_manual = mode == "manual_fallback"

        job_data = {
            "job_id": job_id,
            "module_id": module.module_id,
            "status": "completed" if is_manual else "queued",
            "mode": mode,
            "created_at": now_iso,
            "started_at": now_iso if is_manual else None,
            "finished_at": now_iso if is_manual else None,
            "target": target,
            "exit_code": 0 if is_manual else None,
            "error": None
        }
        if manual_instructions:
            job_data["instructions"] = manual_instructions

        future: Optional[Future] = None

        with self.lock:
            if self.shutting_down:
                raise RuntimeError("Server is shutting down. Cannot accept new jobs.")

            job_dir = self._create_job_dir(job_id)
            self.job_dirs[job_id] = job_dir
            self.jobs[job_id] = job_data
            self._persist_job(job_id, job_data)

            if not is_manual:
                try:
                    future = self.worker_pool.submit(self._run_job_task, job_id, module, target)
                except RuntimeError:
                    job_data["status"] = "interrupted"
                    job_data["finished_at"] = datetime.now(timezone.utc).isoformat()
                    job_data["error"] = "Job submission interrupted during server shutdown."
                    self._persist_job(job_id, job_data)
                    raise

                self.futures[job_id] = future

        if future is not None:
            future.add_done_callback(lambda _: self._remove_future(job_id))

        return job_id

    def _run_job_task(self, job_id: str, module: ModuleDefinition, target: str):
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

        process = None
        try:
            pid, process = ExecutionEngine.run_process(
                module.execution.executable,
                module.execution.args,
                target,
                stdout_path,
                stderr_path
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

            timeout_sec = module.execution.timeout_seconds or 300
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
                            job["error"] = "Server shutdown interrupted active job."
                        elif job["status"] in {"cancelling", "cancelled"}:
                            job["status"] = "cancelled"
                        else:
                            job["status"] = "timed_out"
                        job["finished_at"] = datetime.now(timezone.utc).isoformat()
                        job["exit_code"] = exit_code
                        self._persist_job(job_id, job)
                return

            with self.lock:
                self.processes.pop(job_id, None)

            finished_iso = datetime.now(timezone.utc).isoformat()

            with self.lock:
                job = self.jobs.get(job_id)
                if not job:
                    return

                current_status = job["status"]
                if self.shutting_down:
                    job["status"] = "interrupted"
                    job["error"] = "Server shutdown interrupted active job."
                elif current_status in {"cancelling", "cancelled"}:
                    job["status"] = "cancelled"
                else:
                    job["status"] = "completed" if exit_code == 0 else "failed"

                job["finished_at"] = finished_iso
                job["exit_code"] = exit_code
                self._persist_job(job_id, job)

        except Exception as e:
            finished_iso = datetime.now(timezone.utc).isoformat()
            with self.lock:
                self.processes.pop(job_id, None)
                job = self.jobs.get(job_id)
                if job:
                    if self.shutting_down:
                        job["status"] = "interrupted"
                        job["error"] = "Server shutdown interrupted active job."
                    elif job["status"] in {"cancelling", "cancelled"}:
                        job["status"] = "cancelled"
                    else:
                        job["status"] = "failed"
                        job["error"] = str(e)
                    job["finished_at"] = finished_iso
                    job["exit_code"] = -1
                    self._persist_job(job_id, job)

    def cancel_job(self, job_id: str) -> bool:
        with self.lock:
            job = self.jobs.get(job_id)
            if not job:
                return False

            status = job["status"]
            if status in {"completed", "failed", "cancelled", "timed_out", "interrupted"}:
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

                proc = self.processes.get(job_id)
                if proc:
                    self._stop_process_group(proc, grace_seconds=2.0)

                job["status"] = "cancelled"
                job["finished_at"] = datetime.now(timezone.utc).isoformat()
                self._persist_job(job_id, job)
                return True

        return False
```

## `horde/server.py`

```python
import shlex
from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from contextlib import asynccontextmanager
from pathlib import Path
import json
from horde.models import ExecutionRequest
from horde.module_registry import ModuleRegistry
from horde.policy import PolicyEngine
from horde.target_validator import TargetValidator
from horde.job_manager import JobManager

BASE_DIR = Path(__file__).resolve().parent.parent
MODULES_DIR = BASE_DIR / "modules"
LOGS_DIR = BASE_DIR / "logs"

@asynccontextmanager
async def lifespan(app: FastAPI):
    registry = ModuleRegistry(MODULES_DIR)
    jobs = JobManager(LOGS_DIR)

    app.state.registry = registry
    app.state.jobs = jobs

    jobs.recover()

    yield

    jobs.shutdown()

app = FastAPI(title="Linux Recon Horde - Local Control Server", version="2.6.0", lifespan=lifespan)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/api/health")
def health_check():
    return {"status": "online", "mode": "local-first", "version": "2.6.0"}

@app.get("/api/modules")
def list_modules(request: Request):
    registry: ModuleRegistry = request.app.state.registry
    registry.refresh()
    return {
        "modules": registry.list_modules(),
        "errors": registry.list_errors()
    }

@app.get("/api/modules/errors")
def list_module_errors(request: Request):
    registry: ModuleRegistry = request.app.state.registry
    return {"errors": registry.list_errors()}

@app.post("/api/jobs", status_code=status.HTTP_202_ACCEPTED)
def create_job(req: ExecutionRequest, request: Request):
    registry: ModuleRegistry = request.app.state.registry
    job_manager: JobManager = request.app.state.jobs

    registry.refresh()
    module = registry.get_module(req.module_id)
    if not module:
        raise HTTPException(status_code=404, detail=f"Module ID '{req.module_id}' not found.")

    allowed, reason = PolicyEngine.validate_execution_policy(module.risk_level, req.user_acknowledged)
    if not allowed:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail={"error": "policy_blocked", "message": reason})

    try:
        validated_target = TargetValidator.validate(req.target, module.target_type)
    except ValueError as ve:
        raise HTTPException(status_code=status.HTTP_400_BAD_REQUEST, detail={"error": "target_validation_failed", "message": str(ve)})

    if req.force_manual:
        formatted_args = [arg.format(target=validated_target) for arg in module.execution.args]
        safe_command = shlex.join([module.execution.executable, *formatted_args])
        manual_runbook = module.execution.manual_runbook or {}

        instructions = {
            "step": manual_runbook.get("step_description", "Manual execution required."),
            "command": safe_command,
            "expected_output": manual_runbook.get("expected_output", "")
        }

        try:
            job_id = job_manager.create_job(module, validated_target, mode="manual_fallback", manual_instructions=instructions)
        except RuntimeError as re:
            raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(re))

        return {
            "job_id": job_id,
            "status": "completed",
            "mode": "manual_fallback",
            "instructions": instructions
        }

    try:
        job_id = job_manager.create_job(module, validated_target, mode="automatic")
    except RuntimeError as re:
        raise HTTPException(status_code=status.HTTP_503_SERVICE_UNAVAILABLE, detail=str(re))

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Job successfully created and enqueued."
    }

@app.get("/api/jobs")
def list_active_jobs(request: Request):
    job_manager: JobManager = request.app.state.jobs
    with job_manager.lock:
        return {"jobs": list(job_manager.jobs.values())}

@app.get("/api/jobs/{job_id}")
def get_job(job_id: str, request: Request):
    job_manager: JobManager = request.app.state.jobs
    with job_manager.lock:
        if job_id in job_manager.jobs:
            return job_manager.jobs[job_id]

    log_files = list(LOGS_DIR.glob(f"**/{job_id}/job.json"))
    if log_files:
        with open(log_files[0], "r", encoding="utf-8") as f:
            return json.load(f)

    raise HTTPException(status_code=404, detail="Job ID not found.")

@app.delete("/api/jobs/{job_id}")
def cancel_job(job_id: str, request: Request):
    job_manager: JobManager = request.app.state.jobs
    success = job_manager.cancel_job(job_id)
    if not success:
        raise HTTPException(status_code=400, detail="Job could not be cancelled (either finished, non-existent, or already cancelled).")
    return {"job_id": job_id, "status": "cancelled"}
```

---

# Codex execution assignment

## Step 1 — Inspect before editing

Inspect the existing repository and compare these canonical files against the current working tree:

- `horde/models.py`
- `horde/target_validator.py`
- `horde/module_registry.py`
- `horde/policy.py`
- `horde/execution_engine.py`
- `horde/job_manager.py`
- `horde/server.py`

If a locked file differs, align it to this handoff unless the repository contains a demonstrably newer correction that preserves every invariant here. Report the diff before changing it.

## Step 2 — Create the test harness

Create:

```text
tests/
├── conftest.py
├── fixtures/
│   ├── success_job.py
│   ├── sleep_job.py
│   ├── fail_job.py
│   ├── output_job.py
│   ├── ignore_sigterm.py
│   ├── spawn_child.py
│   └── record_argv.py
├── test_target_validator.py
├── test_module_registry.py
├── test_job_manager.py
└── test_api.py
```

All fixtures must be harmless local child processes only.

## Step 3 — Required tests

Implement and execute tests for all of the following:

1. FastAPI lifespan startup/shutdown using `TestClient` as a context manager.
2. `GET /api/health` returns `2.6.0`.
3. Valid module discovery.
4. Malformed JSON module error collection.
5. Duplicate module ID detection.
6. Valid `hostname` target.
7. Valid `domain` target.
8. Valid IPv4.
9. Valid IPv6.
10. Valid generic IP.
11. Valid CIDR.
12. Valid HTTP/HTTPS URL.
13. Invalid targets rejected for every target type.
14. High/Critical module without acknowledgement returns 403.
15. High/Critical module with acknowledgement can proceed.
16. Automatic execution uses structured argv and never a shell.
17. URL containing shell metacharacters remains one argv value.
18. A malicious-looking URL must not create files, execute substitutions, or expand environment variables.
19. `queued -> running -> completed`.
20. `queued -> cancelled`.
21. `running -> cancelled`.
22. `running -> timed_out`.
23. Cancellation precedence over timeout.
24. Missing executable -> failed job.
25. Nonzero exit -> failed job.
26. `stdout.log` and `stderr.log` persisted to UUID job directory.
27. `job.json` valid after each terminal transition.
28. Manual fallback produces a UUID audit record.
29. Manual fallback has `mode=manual_fallback`, `status=completed`, `exit_code=0`.
30. Manual fallback command uses `shlex.join` safe rendering.
31. Rapid short-job hammer test leaves `JobManager.futures == {}`.
32. Four simultaneous active workers plus a fifth queued job.
33. Queued future cancellation prevents execution.
34. Cancellation during the Popen registration window.
35. Shutdown during the Popen registration window.
36. SIGTERM-resistant fixture escalates to SIGKILL.
37. Spawned child process is terminated with its process group.
38. Graceful shutdown leaves no queued/running/cancelling jobs.
39. Queued jobs during shutdown normalize to `interrupted`.
40. Running jobs during shutdown normalize to `interrupted`.
41. `create_job` racing shutdown returns/reaches the 503 path and creates no orphan queued record.
42. Executor submission failure produces durable `interrupted`, not dangling queued state.
43. Restart recovery converts persisted `queued` -> `interrupted`.
44. Restart recovery converts persisted `running` -> `interrupted`.
45. Restart recovery converts persisted `cancelling` -> `interrupted`.
46. Restart recovery does not rerun interrupted jobs.
47. Completed/failed/cancelled/timed_out historical jobs remain terminal on recovery.
48. Fast-completing Future callback ordering leaves no retained Future.
49. No leaked child processes after test suite.
50. Job paths remain fixed to the creation-day UUID directory across state transitions.

## Shell-boundary proof test

Use `record_argv.py` or equivalent to record `sys.argv` to a temporary JSON file. Submit a valid URL containing shell-significant characters in components/query data (percent-encode characters when required to keep it a valid URL), then assert:

- the entire target is exactly one argument;
- no shell expansion occurred;
- no unrelated file was created;
- environment references were not expanded;
- automatic execution remains `shell=False` behavior.

Do not create or use any payload that touches external hosts.

## Step 4 — Test commands

Use the repository's existing environment/dependency workflow where present. Otherwise create a local venv only if needed.

Run at minimum:

```bash
pytest -q
```

Then for release evidence:

```bash
pytest -vv
```

If the repo already uses lint/type-check tooling, also run the existing configured commands. Do not introduce a new framework solely for this handoff.

## Failure protocol

For every failure:

1. Reproduce the failing test alone.
2. Identify root cause.
3. Determine whether the test is wrong or locked code contains a real defect.
4. Patch only the minimum necessary code.
5. Show the exact diff.
6. Rerun the isolated test.
7. Rerun the full suite.
8. Do not silently weaken assertions to obtain green tests.

## Release gates

Do not call this complete until all are true:

```text
0 failed tests
0 test errors
0 leaked subprocesses/process groups
0 retained completed Futures
0 queued/running/cancelling jobs after shutdown
0 orphan queued job records from shutdown races
restart recovery never reruns interrupted work
shell-boundary proof passes
manual fallback audit persistence passes
```

## Required completion report

Return:

1. Current branch and starting commit.
2. Every created/modified file.
3. Diff summary.
4. Test count and exact pytest result.
5. Every bug discovered.
6. Every production-source change made because of a failing test, with justification.
7. Evidence that subprocesses/process groups are gone after tests.
8. Evidence `JobManager.futures` is empty after completed work.
9. Evidence shutdown leaves no active/queued state.
10. `git status`.
11. Clear completion state: `BLOCKED`, `PARTIAL`, or `READY_FOR_V2.6.0_TAG`.

Do **not** merge, tag, release, deploy, or push additional branches unless explicitly instructed after the test report.
