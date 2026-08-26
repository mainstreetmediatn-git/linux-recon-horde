$ErrorActionPreference = 'Stop'

$RootDir = Split-Path -Parent $PSScriptRoot
Set-Location $RootDir

if (-not (Get-Command docker -ErrorAction SilentlyContinue)) {
    throw 'Docker CLI not found. Install Docker Desktop and enable Linux containers/WSL2.'
}

docker info *> $null
if ($LASTEXITCODE -ne 0) {
    throw 'Docker Desktop is not running or the Docker daemon is unavailable.'
}

New-Item -ItemType Directory -Force -Path 'logs' | Out-Null
New-Item -ItemType Directory -Force -Path 'modules' | Out-Null

if (-not (Test-Path '.env')) {
    Copy-Item '.env.example' '.env'
    Write-Host 'Created .env from .env.example'
}

docker compose up --build -d
if ($LASTEXITCODE -ne 0) {
    throw 'docker compose up failed.'
}

Write-Host 'Waiting for Linux Recon Horde health endpoint...'
for ($i = 0; $i -lt 30; $i++) {
    try {
        $health = Invoke-RestMethod -Uri 'http://127.0.0.1:8787/api/health' -TimeoutSec 2
        if ($health.status -eq 'online') {
            Write-Host 'Linux Recon Horde is online at http://127.0.0.1:8787'
            exit 0
        }
    } catch {
        Start-Sleep -Seconds 1
    }
}

Write-Error 'Container started but health check did not become ready.'
docker compose ps
docker compose logs --tail=100 horde
exit 1
