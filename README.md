# Linux Recon Horde

> A hardened, local-first, dual-mode reconnaissance orchestration engine built for Python 3.11+.

**Linux Recon Horde** bridges the gap between autonomous AI agent tooling and rigorous human-in-the-loop operational security. It provides a structured, race-condition-free execution environment for running recon modules with strict target validation, process-group isolation, durable persistence, and an integrated Model Context Protocol (MCP) gateway.

---

## 🌟 Core Architecture & Features

- **Dual-Mode Orchestration Architecture**: Seamlessly switches between automated background execution via a bounded thread pool and safe manual fallback runbooks—both bound to the exact same validation and policy pipeline.
- **Defensive Concurrency & Lifecycle Safety**: Features atomic create-vs-shutdown boundaries, reversed completion-callback registration to eliminate retention leaks, and graceful shutdown normalization of queued/running tasks.
- **Process Isolation & Supervision**: Spawns jobs in isolated process sessions (`start_new_session=True`) with multi-stage teardown escalation (`SIGTERM` → graceful grace period → `SIGKILL`), preventing orphan processes and zombies.
- **Robust Target Validation**: Strict validation schemas parsing IP addresses (IPv4/IPv6), CIDR blocks, hostnames, domains, and URLs to block malformed inputs.
- **Shell-Injection Defense**: Strictly avoids `shell=True`. Automated commands execute via structured `argv` arrays, and manual runbooks are safely rendered via `shlex.join`.
- **Durable Disk Audit Trails**: Every job receives an isolated, timestamped log directory containing atomic `job.json` states alongside dedicated `stdout.log` and `stderr.log` streams.
- **Model Context Protocol (MCP) Integration**: Built-in MCP gateway allows compatible AI clients to safely interact with the Horde while programmatically restricting high-risk modules and preserving human approval boundaries.

---

## 🚀 Getting Started

### Prerequisites

- Python 3.11 or higher

### Installation

Clone the repository and install the package in editable mode with development dependencies:

```bash
git clone https://github.com/mainstreetmediatn-git/linux-recon-horde.git
cd linux-recon-horde

python -m venv .venv
source .venv/bin/activate
pip install --upgrade pip
pip install -e '.[dev]'
```
