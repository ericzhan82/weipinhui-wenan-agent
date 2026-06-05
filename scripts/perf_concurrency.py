from __future__ import annotations

from concurrent.futures import ThreadPoolExecutor, as_completed
from pathlib import Path
import os
import statistics
import sys
import time
from uuid import uuid4

import requests


ROOT = Path(__file__).resolve().parents[1]


def env_value(name: str, default: str = "") -> str:
    if os.getenv(name):
        return os.environ[name]
    env_path = ROOT / ".env"
    if env_path.exists():
        for line in env_path.read_text(encoding="utf-8", errors="ignore").splitlines():
            if line.startswith(f"{name}="):
                return line.split("=", 1)[1].strip()
    return default


def login(base: str) -> dict[str, str]:
    response = requests.post(
        f"{base}/auth/login",
        json={
            "email": env_value("SMOKE_EMAIL", env_value("ADMIN_EMAIL", "admin@example.com")),
            "password": env_value("SMOKE_PASSWORD", env_value("ADMIN_PASSWORD", "change_me_admin_password")),
        },
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    return {
        "Authorization": f"Bearer {payload['access_token']}",
        "X-Workspace-Id": str(payload["user"]["workspaces"][0]["id"]),
    }


def timed_get(base: str, headers: dict[str, str], path: str) -> tuple[str, float, int]:
    started = time.perf_counter()
    response = requests.get(f"{base}{path}", headers=headers, timeout=10)
    elapsed = time.perf_counter() - started
    return path, elapsed, response.status_code


def create_product(base: str, headers: dict[str, str], run_id: str, index: int) -> int:
    response = requests.post(
        f"{base}/products",
        headers=headers,
        json={
            "style_no": f"PERF-{run_id}-{index:03d}",
            "product_no": f"P-{run_id}-{index:03d}",
            "category_3": "外套",
            "category_4": "防晒衣",
            "age_range": "中大童",
            "gender": "女童",
            "season": "夏季",
            "scene": "出游",
            "fba": "清凉防晒，透气不闷，轻薄好穿",
            "remark": "performance concurrency test",
            "skus": [{"sku_no": f"SKC-{run_id}-{index:03d}", "color_name": "浅蓝", "color_code": "BL"}],
        },
        timeout=10,
    )
    response.raise_for_status()
    return int(response.json()["id"])


def wait_batch(base: str, headers: dict[str, str], batch_no: str, timeout_seconds: int) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = requests.get(f"{base}/copy-batches/{batch_no}", headers=headers, timeout=10)
        response.raise_for_status()
        detail = response.json()
        status = detail["batch"]["status"]
        if status in {"completed", "completed_with_errors", "canceled"}:
            return detail
        time.sleep(2)
    raise TimeoutError(f"batch timeout: {batch_no}")


def percentile(values: list[float], pct: float) -> float:
    if not values:
        return 0
    values = sorted(values)
    index = min(len(values) - 1, int(round((len(values) - 1) * pct)))
    return values[index]


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/api"
    product_count = int(os.getenv("PERF_PRODUCT_COUNT", "50"))
    headers = login(base)
    run_id = uuid4().hex[:8]

    for index in range(product_count):
        create_product(base, headers, run_id, index)

    create_response = requests.post(
        f"{base}/copy-batches",
        headers=headers,
        json={
            "keyword": f"PERF-{run_id}",
            "context_status": "ready",
            "copy_state": "not_generated",
            "overwrite_existing": False,
            "use_hot_search": False,
        },
        timeout=10,
    )
    create_response.raise_for_status()
    batch = create_response.json()

    paths = ["/health", "/products", "/copy-batches", "/llm/status"]
    latencies: list[float] = []
    statuses: list[int] = []
    with ThreadPoolExecutor(max_workers=8) as executor:
        futures = [executor.submit(timed_get, base, headers, paths[index % len(paths)]) for index in range(40)]
        for future in as_completed(futures):
            _, elapsed, status = future.result()
            latencies.append(elapsed)
            statuses.append(status)

    if any(status >= 500 for status in statuses):
        raise AssertionError(f"5xx seen during concurrent reads: {statuses}")
    p95 = percentile(latencies, 0.95)
    if p95 > float(os.getenv("PERF_P95_SECONDS", "2")):
        raise AssertionError(f"API P95 too slow: {p95:.3f}s")

    detail = wait_batch(base, headers, batch["batch_no"], int(os.getenv("PERF_BATCH_TIMEOUT_SECONDS", "240")))
    final_batch = detail["batch"]
    final_total = (
        final_batch["success_count"]
        + final_batch["failed_count"]
        + final_batch["skipped_count"]
        + final_batch["canceled_count"]
    )
    if final_batch["total_count"] != product_count or final_total != product_count:
        raise AssertionError(f"batch count mismatch: {final_batch}")
    if final_batch["failed_count"] != 0:
        raise AssertionError(f"batch has failures: {final_batch}")

    print(
        {
            "run_id": run_id,
            "product_count": product_count,
            "batch_no": batch["batch_no"],
            "api_p95_seconds": round(p95, 3),
            "api_avg_seconds": round(statistics.mean(latencies), 3),
            "batch_status": final_batch["status"],
        }
    )
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
