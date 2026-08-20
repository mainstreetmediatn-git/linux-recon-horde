from uuid import uuid4

import httpx
import pytest

from horde.config import Settings
from horde.core.models import Job, JobState
from horde.db import SupabaseClient
from horde.jobs.supabase_queue import SupabaseJobQueue


class FakeSupabaseClient:
    def __init__(self):
        self.tables = []
        self.rpcs = []
        self.rows = []

    async def table(self, table, method="GET", payload=None, **params):
        self.tables.append((table, method, payload, params))
        if method == "GET" and params.get("select") == "attempt_count,max_attempts":
            return [{"attempt_count": 1, "max_attempts": 3}]
        if method == "GET":
            return self.rows
        return None

    async def rpc(self, function, payload):
        self.rpcs.append((function, payload))
        if function == "recover_expired_jobs":
            return 2
        return self.rows


def make_job() -> Job:
    return Job(project_id=uuid4(), target="example.com", tool="dns")


@pytest.mark.asyncio
async def test_supabase_queue_uses_atomic_rpc_and_persists_state():
    client = FakeSupabaseClient()
    queue = SupabaseJobQueue(client)
    job = make_job()
    client.rows = [job.model_dump(mode="json")]

    assert await queue.enqueue(job) == job
    assert await queue.recover_expired() == 2
    assert await queue.claim("worker-1") == job
    await queue.mark_running(job.id)
    await queue.complete(job.id)
    await queue.fail(job.id, "temporary", retry=True)

    assert client.rpcs == [
        ("recover_expired_jobs", {}),
        ("claim_job", {"p_worker_id": "worker-1", "p_lease_seconds": 60}),
    ]
    assert any(call[0:2] == ("jobs", "POST") for call in client.tables)
    assert client.tables[-1][3]["id"] == f"eq.{job.id}"
    assert client.tables[-1][2]["state"] == JobState.QUEUED.value


@pytest.mark.asyncio
async def test_supabase_client_selects_custom_schema_headers():
    requests = []

    async def handler(request: httpx.Request) -> httpx.Response:
        requests.append(request)
        return httpx.Response(200, json=[])

    settings = Settings(
        _env_file=None,
        supabase_url="https://example.supabase.co",
        supabase_service_role_key="test-key",
    )
    client = SupabaseClient(settings, transport=httpx.MockTransport(handler))
    try:
        await client.table("jobs")
        await client.rpc("recover_expired_jobs", {})
    finally:
        await client.close()

    assert requests[0].headers["Accept-Profile"] == "horde"
    assert requests[1].headers["Content-Profile"] == "horde"
