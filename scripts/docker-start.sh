#!/usr/bin/env bash
set -euo pipefail

ROOT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT_DIR"

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker is required. Install Docker Engine with the Compose plugin first." >&2
  exit 1
fi

if ! docker info >/dev/null 2>&1; then
  echo "Docker daemon is not reachable. Start Docker and ensure your user can access it." >&2
  exit 1
fi

mkdir -p logs modules

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

docker compose up --build -d

echo "Waiting for Linux Recon Horde health endpoint..."
for _ in $(seq 1 30); do
  if curl --fail --silent http://127.0.0.1:8787/api/health >/dev/null 2>&1; then
    echo "Linux Recon Horde is online at http://127.0.0.1:8787"
    exit 0
  fi
  sleep 1
done

echo "Container started but health check did not become ready." >&2
docker compose ps
docker compose logs --tail=100 horde
exit 1
