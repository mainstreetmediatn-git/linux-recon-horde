import json
import shlex
from contextlib import asynccontextmanager
from pathlib import Path

from fastapi import FastAPI, HTTPException, Request, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import PlainTextResponse

from horde.local_engine.job_manager import JobManager
from horde.local_engine.models import ExecutionRequest
from horde.local_engine.module_registry import ModuleRegistry
from horde.local_engine.policy import PolicyEngine
from horde.local_engine.target_validator import TargetValidator

BASE_DIR = Path(__file__).resolve().parent.parent.parent
MODULES_DIR = BASE_DIR / "modules"
LOGS_DIR = BASE_DIR / "logs"
ENGINE_VERSION = "2.6.0"
API_VERSION = "2.7.0-dev"


@asynccontextmanager
async def lifespan(app: FastAPI):
    registry = ModuleRegistry(MODULES_DIR)
    jobs = JobManager(LOGS_DIR)

    app.state.registry = registry
    app.state.jobs = jobs
    jobs.recover()

    yield

    jobs.shutdown()


app = FastAPI(
    title="Linux Recon Horde - Local Control Server",
    version=API_VERSION,
    lifespan=lifespan,
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=["http://localhost:3000", "http://127.0.0.1:3000"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)


@app.get("/api/health")
def health_check():
    return {
        "status": "online",
        "mode": "local-first",
        "engine_version": ENGINE_VERSION,
        "api_version": API_VERSION,
    }


@app.get("/api/modules")
def list_modules(request: Request):
    registry: ModuleRegistry = request.app.state.registry
    registry.refresh()
    return {
        "modules": registry.list_modules(),
        "errors": registry.list_errors(),
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
        raise HTTPException(
            status_code=404,
            detail=f"Module ID '{req.module_id}' not found.",
        )

    allowed, reason = PolicyEngine.validate_execution_policy(
        module.risk_level,
        req.user_acknowledged,
    )
    if not allowed:
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={"error": "policy_blocked", "message": reason},
        )

    try:
        validated_target = TargetValidator.validate(
            req.target,
            module.target_type,
        )
    except ValueError as exc:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "error": "target_validation_failed",
                "message": str(exc),
            },
        ) from exc

    if req.force_manual:
        formatted_args = [
            arg.format(target=validated_target)
            for arg in module.execution.args
        ]
        safe_command = shlex.join(
            [module.execution.executable, *formatted_args]
        )
        manual_runbook = module.execution.manual_runbook or {}
        instructions = {
            "step": manual_runbook.get(
                "step_description",
                "Manual execution required.",
            ),
            "command": safe_command,
            "expected_output": manual_runbook.get("expected_output", ""),
        }

        try:
            job_id = job_manager.create_job(
                module,
                validated_target,
                mode="manual_fallback",
                manual_instructions=instructions,
            )
        except RuntimeError as exc:
            raise HTTPException(
                status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
                detail=str(exc),
            ) from exc

        return {
            "job_id": job_id,
            "status": "completed",
            "mode": "manual_fallback",
            "instructions": instructions,
        }

    try:
        job_id = job_manager.create_job(
            module,
            validated_target,
            mode="automatic",
        )
    except RuntimeError as exc:
        raise HTTPException(
            status_code=status.HTTP_503_SERVICE_UNAVAILABLE,
            detail=str(exc),
        ) from exc

    return {
        "job_id": job_id,
        "status": "queued",
        "message": "Job successfully created and enqueued.",
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
        with open(log_files[0], "r", encoding="utf-8") as handle:
            return json.load(handle)

    raise HTTPException(status_code=404, detail="Job ID not found.")


@app.get(
    "/api/jobs/{job_id}/stdout",
    response_class=PlainTextResponse,
)
def get_job_stdout(job_id: str, request: Request):
    return _read_job_stream(job_id, "stdout.log", request)


@app.get(
    "/api/jobs/{job_id}/stderr",
    response_class=PlainTextResponse,
)
def get_job_stderr(job_id: str, request: Request):
    return _read_job_stream(job_id, "stderr.log", request)


def _read_job_stream(job_id: str, filename: str, request: Request) -> str:
    job_manager: JobManager = request.app.state.jobs
    job_dir = job_manager.get_job_dir(job_id)
    if not job_dir:
        raise HTTPException(status_code=404, detail="Job ID not found.")

    path = job_dir / filename
    if not path.exists():
        return ""

    return path.read_text(encoding="utf-8", errors="replace")


@app.delete("/api/jobs/{job_id}")
def cancel_job(job_id: str, request: Request):
    job_manager: JobManager = request.app.state.jobs
    success = job_manager.cancel_job(job_id)
    if not success:
        raise HTTPException(
            status_code=400,
            detail=(
                "Job could not be cancelled "
                "(either finished, non-existent, or already cancelled)."
            ),
        )
    return {"job_id": job_id, "status": "cancelled"}
