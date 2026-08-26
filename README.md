# Linux Recon Horde

Linux Recon Horde is a local-first reconnaissance orchestration engine for owned systems, approved labs, and explicitly authorized security assessments.

Version **2.6.0** adds the hardened local execution engine plus a single canonical **Linux container image** that runs on both Linux Docker Engine and Windows Docker Desktop/WSL2.

## Current architecture

The project includes:

- FastAPI local control server
- strict target validation
- explicit risk acknowledgement for high-risk modules
- bounded worker execution
- subprocess isolation and lifecycle management
- cancellation, timeout, recovery, and durable job logs
- JSON module registry
- MCP gateway
- Docker packaging for Linux and Windows hosts

The HTTP API listens on port `8787` by default. The health endpoint is:

```text
GET /api/health
```

## Safety model

Use Linux Recon Horde only against infrastructure you own or have explicit authorization to assess. The engine preserves policy checks, target validation, process isolation, job evidence, and operator acknowledgement boundaries. Do not weaken these controls when adding modules.

## Docker image

The canonical runtime is a Linux image based on Python 3.11 slim. Windows users run the same Linux image through Docker Desktop using the WSL2/Linux-container backend.

The image includes the runtime dependencies plus common low-level networking utilities required by authorized modules:

- Python 3.11
- FastAPI / Uvicorn
- Pydantic
- HTTPX
- MCP SDK
- Nmap
- DNS utilities
- ping
- netcat
- curl
- tini

The container runs as a non-root user. Compose drops all Linux capabilities and restores only `NET_RAW`, which is useful for common network diagnostics without granting privileged-container access.

## Quick start — Linux

Requirements:

- Docker Engine
- Docker Compose plugin (`docker compose`)

Clone the repository and switch to the release branch or merged release commit, then run:

```bash
chmod +x scripts/docker-start.sh
./scripts/docker-start.sh
```

Or manually:

```bash
mkdir -p logs modules
cp .env.example .env
docker compose up --build -d
curl http://127.0.0.1:8787/api/health
```

Stop the service with:

```bash
docker compose down
```

## Quick start — Windows 11 / Windows 10

Requirements:

- Docker Desktop
- WSL2 enabled
- Docker Desktop configured for Linux containers

From PowerShell in the repository directory:

```powershell
Set-ExecutionPolicy -Scope Process Bypass
.\scripts\docker-start.ps1
```

Or manually:

```powershell
New-Item -ItemType Directory -Force logs,modules
Copy-Item .env.example .env
docker compose up --build -d
Invoke-RestMethod http://127.0.0.1:8787/api/health
```

Stop it with:

```powershell
docker compose down
```

The Windows host is not running a Windows container. Docker Desktop runs the same Linux Recon Horde image used on Linux, which keeps dependencies and execution behavior consistent across hosts.

## Modules

Runtime module definitions live in the host `modules/` directory and are mounted read-only into `/app/modules` inside the container.

Each module is a JSON document validated by the Horde module schema. Keep executable names Linux-compatible because execution occurs inside the Linux container even when the host is Windows.

Example layout:

```text
modules/
  discovery/
    example.json
logs/
```

The repository intentionally does not ship active external-target modules as part of the packaging layer. Add only approved modules appropriate to your lab or engagement.

## Persistent data

Compose mounts:

```text
./logs    -> /app/logs
./modules -> /app/modules (read-only)
```

Job state, stdout, stderr, and recovery metadata remain on the host through the `logs` mount.

## Environment

Copy `.env.example` to `.env` before launch. Secrets must never be committed.

```env
OPENAI_API_KEY=
```

The server uses these container defaults:

```text
HORDE_HOST=0.0.0.0
HORDE_PORT=8787
```

## Native Python development

Python 3.11 or 3.12 is supported.

```bash
python -m venv .venv
source .venv/bin/activate
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
pytest
horde-server
```

On PowerShell without Docker:

```powershell
py -3.11 -m venv .venv
.\.venv\Scripts\Activate.ps1
python -m pip install --upgrade pip
python -m pip install -e '.[dev]'
pytest
horde-server
```

Native Windows execution is intended primarily for development. Docker is the recommended Windows runtime because module executables and process semantics remain Linux-native.

## Build and verification

Build the image directly:

```bash
docker build -t linux-recon-horde:2.6.0 .
```

Validate Compose configuration:

```bash
docker compose config
```

Check the running container:

```bash
docker compose ps
docker compose logs --tail=100 horde
curl http://127.0.0.1:8787/api/health
```

GitHub Actions validates Python 3.11 and 3.12, compiles the package, runs pytest, builds the Linux Docker image, starts it, and verifies the health endpoint.

## Security and container boundaries

The Compose configuration uses:

- non-root application user
- `no-new-privileges`
- all capabilities dropped by default
- only `NET_RAW` restored
- read-only module mount
- persistent isolated log mount
- PID 1 signal handling through `tini`
- application health checks

Do not add `privileged: true`, mount the Docker socket, or weaken the execution policy to make a module work. Add only the narrowly required capability or dependency and document why it is necessary.

## Project status

The v2.6 execution branch contains the local engine, API, lifecycle controls, recovery logic, and MCP gateway. The `packaging/windows-docker-v2.6.0` branch adds the cross-host Docker release layer, updated dependency metadata, CI Docker verification, launch scripts, and current documentation.

See `CODEX_HANDOFF_V2.6.0.md` for the preserved engineering handoff and `docs/ARCHITECTURE.md` for architecture background.
