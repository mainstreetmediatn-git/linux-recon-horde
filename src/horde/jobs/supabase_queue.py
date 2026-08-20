"""Supabase-backed lease queue using the database's atomic claim functions."""

from uuid import UUID

from horde.core.models import Job, JobState, utcnow
from horde.db.client import SupabaseClient


class SupabaseJobQueue:
    def __init__(self, client: SupabaseClient) -> None:
        self.client = client

    async def enqueue(self, job: Job) -> Job:
        await self.client.table("jobs", method="POST", payload=job.model_dump(mode="json"))
        return job

    async def recover_expired(self) -> int:
        result = await self.client.rpc("recover_expired_jobs", {})
        if isinstance(result, int):
            return result
        if isinstance(result, list) and result and isinstance(result[0], int):
            return result[0]
        raise ValueError(f"unexpected recover_expired_jobs response: {result!r}")

    async def claim(self, worker_id: str, lease_seconds: int = 60) -> Job | None:
        result = await self.client.rpc(
            "claim_job",
            {"p_worker_id": worker_id, "p_lease_seconds": lease_seconds},
        )
        if not result:
            return None
        row = result[0] if isinstance(result, list) else result
        return Job.model_validate(row)

    async def mark_running(self, job_id: UUID) -> None:
        await self._update(job_id, {"state": JobState.RUNNING.value})

    async def complete(self, job_id: UUID) -> None:
        await self._update(job_id, {"state": JobState.SUCCEEDED.value, "lease_expires_at": None})

    async def fail(self, job_id: UUID, error: str, retry: bool = True) -> None:
        rows = await self.client.table(
            "jobs",
            select="attempt_count,max_attempts",
            id=f"eq.{job_id}",
        )
        if not rows:
            raise KeyError(f"job not found: {job_id}")
        current = rows[0]
        should_retry = retry and current["attempt_count"] < current["max_attempts"]
        await self._update(
            job_id,
            {
                "state": JobState.QUEUED.value if should_retry else JobState.FAILED.value,
                "last_error": error[:2000],
                "worker_id": None,
                "lease_expires_at": None,
            },
        )

    async def get(self, job_id: UUID) -> Job:
        rows = await self.client.table("jobs", id=f"eq.{job_id}")
        if not rows:
            raise KeyError(f"job not found: {job_id}")
        return Job.model_validate(rows[0])

    async def list(self, state: JobState | None = None) -> list[Job]:
        params: dict[str, str] = {"order": "created_at.asc"}
        if state is not None:
            params["state"] = f"eq.{state.value}"
        rows = await self.client.table("jobs", **params) or []
        return [Job.model_validate(row) for row in rows]

    async def _update(self, job_id: UUID, values: dict[str, object]) -> None:
        values["updated_at"] = utcnow().isoformat()
        await self.client.table("jobs", method="PATCH", payload=values, id=f"eq.{job_id}")
