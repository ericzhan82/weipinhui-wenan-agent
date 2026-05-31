#!/usr/bin/env bash
set -euo pipefail

ROOT="$(cd "$(dirname "${BASH_SOURCE[0]}")/.." && pwd)"
cd "$ROOT"

cleanup=0
if [[ "${1:-}" == "--cleanup" ]]; then
  cleanup=1
fi

if ! command -v docker >/dev/null 2>&1; then
  echo "Docker CLI is not available. Install/start Docker, then rerun this script." >&2
  exit 1
fi

if ! docker_version_output="$(docker version --format '{{.Server.Version}}' 2>&1)"; then
  echo "Docker Engine is not ready." >&2
  echo "docker version output:" >&2
  echo "$docker_version_output" >&2
  echo "Start Docker and wait until the engine is running, then rerun this script." >&2
  exit 1
fi
if [[ -z "$docker_version_output" || "$docker_version_output" =~ (request\ returned|unable|Cannot\ connect|daemon) ]]; then
  echo "Docker Engine is not ready." >&2
  echo "docker version output:" >&2
  echo "$docker_version_output" >&2
  echo "Start Docker and wait until the engine is running, then rerun this script." >&2
  exit 1
fi
echo "Docker Engine OK: $docker_version_output"

if [[ ! -f .env ]]; then
  cp .env.example .env
  echo "Created .env from .env.example"
fi

docker compose up -d --build
docker compose ps

backend_port="$(grep -E '^BACKEND_PORT=' .env | tail -1 | cut -d= -f2- || true)"
frontend_port="$(grep -E '^FRONTEND_PORT=' .env | tail -1 | cut -d= -f2- || true)"
backend_port="${backend_port:-8000}"
frontend_port="${frontend_port:-80}"

wait_endpoint() {
  local url="$1"
  local name="$2"
  for _ in $(seq 1 60); do
    if curl -fsS "$url" >/dev/null; then
      echo "$name OK"
      return 0
    fi
    sleep 2
  done
  echo "$name did not become ready: $url" >&2
  return 1
}

wait_endpoint "http://127.0.0.1:${backend_port}/api/health" "Backend health"
wait_endpoint "http://127.0.0.1:${backend_port}/api/llm/status" "LLM status"
wait_endpoint "http://127.0.0.1:${frontend_port}" "Frontend"

python scripts/smoke_api.py "http://127.0.0.1:${backend_port}/api"

echo "Docker Compose verification passed."

if [[ "$cleanup" == "1" ]]; then
  docker compose down
  echo "Docker Compose services stopped."
fi
