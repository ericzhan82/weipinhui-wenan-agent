param(
    [switch]$Cleanup
)

$ErrorActionPreference = "Stop"
$Root = Split-Path -Parent (Split-Path -Parent $MyInvocation.MyCommand.Path)
Set-Location $Root

if (-not (Test-Path ".env")) {
    Write-Host "No .env found; copying .env.example for local validation."
    Copy-Item ".env.example" ".env"
}

Write-Host "== Backend tests =="
python -m pytest

Write-Host "== Frontend build =="
Push-Location frontend
npm.cmd run build
Pop-Location

Write-Host "== Delivery check =="
python scripts/check_delivery.py

Write-Host "== Docker compose build/start =="
docker compose up -d --build
docker compose ps

$backendPort = "8000"
if (Test-Path ".env") {
    foreach ($line in Get-Content ".env") {
        if ($line -match "^BACKEND_PORT=(.+)$") { $backendPort = $Matches[1].Trim() }
    }
}
$apiBase = "http://127.0.0.1:$backendPort/api"

Write-Host "== API smoke test =="
python scripts/smoke_api.py $apiBase

Write-Host "== Performance and concurrency test =="
python scripts/perf_concurrency.py $apiBase

Write-Host "FULL LOCAL TEST SUITE PASSED"

if ($Cleanup) {
    Write-Host "Stopping containers without deleting volumes..."
    docker compose down
}
