import os
from typing import Any

import httpx
from mcp.server import MCPServer

HORDE_API_URL = os.getenv("HORDE_API_URL", "http://127.0.0.1:8787").rstrip("/")
REQUEST_TIMEOUT = float(os.getenv("HORDE_MCP_HTTP_TIMEOUT", "15"))

mcp = MCPServer(
    "Linux Recon Horde",
    instructions=(
        "Operate only on owned or explicitly authorized targets. "
        "The MCP gateway permits Low/Medium reconnaissance modules only. "
        "High/Critical modules require the direct Horde approval path."
    ),
)


async def _request(
    method: str,
    path: str,
    *,
    json_body: dict[str, Any] | None = None,
) -> Any:
    async with httpx.AsyncClient(timeout=REQUEST_TIMEOUT) as client:
        response = await client.request(
            method,
            f"{HORDE_API_URL}{path}",
            json=json_body,
        )

    if response.status_code >= 400:
        try:
            detail = response.json()
        except ValueError:
            detail = response.text
        raise RuntimeError(
            f"Horde API returned HTTP {response.status_code}: {detail}"
        )

    content_type = response.headers.get("content-type", "")
    if "application/json" in content_type:
        return response.json()
    return response.text


async def _get_module(module_id: str) -> dict[str, Any]:
    payload = await _request("GET", "/api/modules")
    for module in payload.get("modules", []):
        if module.get("module_id") == module_id:
            return module
    raise ValueError(f"Unknown Horde module: {module_id}")


@mcp.tool()
async def horde_health() -> dict[str, Any]:
    """Return local Horde engine/API health information."""
    return await _request("GET", "/api/health")


@mcp.tool()
async def horde_list_modules() -> dict[str, Any]:
    """List validated Horde modules and module-definition errors."""
    return await _request("GET", "/api/modules")


@mcp.tool()
async def horde_submit_job(
    module_id: str,
    target: str,
    force_manual: bool = False,
) -> dict[str, Any]:
    """Submit an authorized Low/Medium reconnaissance job.

    High and Critical modules are intentionally not executable through MCP.
    They must use the direct operator approval path in the Horde API/UI.
    """
    module = await _get_module(module_id)
    risk_level = module.get("risk_level")
    if risk_level in {"High", "Critical"}:
        raise PermissionError(
            f"Module {module_id!r} is {risk_level} risk and cannot be "
            "executed through the autonomous MCP gateway. Use the direct "
            "Horde approval path."
        )

    return await _request(
        "POST",
        "/api/jobs",
        json_body={
            "module_id": module_id,
            "target": target,
            "force_manual": force_manual,
            "user_acknowledged": False,
        },
    )


@mcp.tool()
async def horde_get_job(job_id: str) -> dict[str, Any]:
    """Return the durable state of a Horde job."""
    return await _request("GET", f"/api/jobs/{job_id}")


@mcp.tool()
async def horde_list_jobs() -> dict[str, Any]:
    """List current and recovered Horde job records."""
    return await _request("GET", "/api/jobs")


@mcp.tool()
async def horde_cancel_job(job_id: str) -> dict[str, Any]:
    """Cancel a queued or running Horde job."""
    return await _request("DELETE", f"/api/jobs/{job_id}")


@mcp.tool()
async def horde_read_stdout(job_id: str) -> str:
    """Read the stdout log for a Horde job."""
    return await _request("GET", f"/api/jobs/{job_id}/stdout")


@mcp.tool()
async def horde_read_stderr(job_id: str) -> str:
    """Read the stderr log for a Horde job."""
    return await _request("GET", f"/api/jobs/{job_id}/stderr")


def main() -> None:
    transport = os.getenv("HORDE_MCP_TRANSPORT", "stdio")
    if transport == "stdio":
        mcp.run(transport="stdio")
    elif transport == "streamable-http":
        mcp.run(
            transport="streamable-http",
            host=os.getenv("HORDE_MCP_HOST", "127.0.0.1"),
            port=int(os.getenv("HORDE_MCP_PORT", "8790")),
        )
    else:
        raise SystemExit(
            "HORDE_MCP_TRANSPORT must be 'stdio' or 'streamable-http'."
        )


if __name__ == "__main__":
    main()
