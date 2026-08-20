"""Small operator CLI; commands default to safe dry-run behavior."""

import asyncio
import json
from uuid import UUID

import typer

from horde.config import get_settings
from horde.core.models import Agent, Job
from horde.db import SupabaseClient
from horde.diagnostics.doctor import doctor
from horde.jobs import SupabaseJobQueue
from horde.jobs.queue import InMemoryJobQueue
from horde.runtime.logging import configure_logging
from horde.runtime.worker import Worker
from horde.scope.models import AuthorizedScope, ScopeKind
from horde.scope.policy import ScopeEngine
from horde.tools.registry import default_registry

app = typer.Typer(help="Authorized Linux reconnaissance orchestration")
scope_app = typer.Typer(help="Inspect authorized scopes")
tools_app = typer.Typer(help="Inspect approved tool adapters")
app.add_typer(scope_app, name="scope")
app.add_typer(tools_app, name="tools")


@app.command("doctor")
def doctor_cmd(json_output: bool = typer.Option(False, "--json")) -> None:
    """Check runtime prerequisites."""
    configure_logging(get_settings().log_level)
    result = doctor(get_settings(), default_registry())
    typer.echo(json.dumps(result) if json_output else "\n".join(f"{item['status']:5} {item['check']}: {item.get('detail', '')}" for item in result))


@scope_app.command("check")
def scope_check(target: str, kind: ScopeKind = ScopeKind.DOMAIN, value: str = "example.com") -> None:
    """Check a target against one explicitly supplied scope."""
    decision = ScopeEngine().check(target, [AuthorizedScope(kind=kind, value=value)])
    typer.echo(decision.model_dump_json())
    raise typer.Exit(code=0 if decision.allowed else 1)


@tools_app.command("list")
def tools_list() -> None:
    typer.echo("\n".join(default_registry().names()))


@app.command()
def worker_once(
    target: str = typer.Option(..., "--target"),
    tool: str = "dns",
    project_id: str = typer.Option(...),
    agent_id: str | None = None,
    backend: str = typer.Option("memory", help="Queue backend: memory or supabase."),
) -> None:
    """Run one job using the local queue or the durable Supabase queue."""
    if backend not in {"memory", "supabase"}:
        raise typer.BadParameter("must be 'memory' or 'supabase'", param_hint="--backend")
    if backend == "supabase":
        result = asyncio.run(_worker_once_supabase(target, tool, project_id, agent_id))
        typer.echo(result.model_dump_json())
        return

    settings = get_settings()
    queue = InMemoryJobQueue()
    agent = Agent(id=UUID(agent_id) if agent_id else UUID(int=0), project_id=UUID(project_id), name="local")
    queue.enqueue(Job(project_id=UUID(project_id), target=target, tool=tool))
    asyncio.run(Worker(agent, queue, [AuthorizedScope(kind=ScopeKind.DOMAIN, value=target)], default_registry(), settings).run_once())
    typer.echo(queue.list()[0].model_dump_json())


async def _worker_once_supabase(
    target: str,
    tool: str,
    project_id: str,
    agent_id: str | None,
) -> Job:
    settings = get_settings()
    project_uuid = UUID(project_id)
    client = SupabaseClient(settings)
    try:
        rows = await client.table(
            "authorized_scopes",
            project_id=f"eq.{project_uuid}",
            active="eq.true",
        )
        scopes = [AuthorizedScope.model_validate(row) for row in rows or []]
        queue = SupabaseJobQueue(client)
        agent = Agent(
            id=UUID(agent_id) if agent_id else UUID(int=0),
            project_id=project_uuid,
            name="supabase-once",
        )
        job = Job(project_id=project_uuid, target=target, tool=tool)
        await queue.enqueue(job)
        await Worker(agent, queue, scopes, default_registry(), settings).run_once()
        return await queue.get(job.id)
    finally:
        await client.close()
