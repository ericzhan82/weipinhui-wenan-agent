#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

if [[ ! -f .env ]]; then
  echo "No .env found; copying .env.example for local validation."
  cp .env.example .env
fi

echo "== Backend tests =="
python -m pytest

echo "== Frontend build =="
(cd frontend && npm run build)

echo "== Delivery check =="
python scripts/check_delivery.py

echo "== Docker compose build/start =="
docker compose up -d --build
docker compose ps

BACKEND_PORT="${BACKEND_PORT:-8000}"
if [[ -f .env ]]; then
  ENV_PORT="$(grep -E '^BACKEND_PORT=' .env | tail -n 1 | cut -d= -f2- || true)"
  if [[ -n "${ENV_PORT}" ]]; then
    BACKEND_PORT="${ENV_PORT}"
  fi
fi
API_BASE="http://127.0.0.1:${BACKEND_PORT}/api"

echo "== API smoke test =="
python scripts/smoke_api.py "$API_BASE"

echo "== Performance and concurrency test =="
python scripts/perf_concurrency.py "$API_BASE"

echo "FULL LOCAL TEST SUITE PASSED"

if [[ "${1:-}" == "--cleanup" ]]; then
  echo "Stopping containers without deleting volumes..."
  docker compose down
fi
