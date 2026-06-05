from io import BytesIO
import json
import os
from pathlib import Path
import sys
import time

from openpyxl import Workbook
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


def hot_search_workbook() -> bytes:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["排名", "搜索词主分类", "关键词", "搜索UV指数", "机会指数", "成交金额指数", "销售量指数"])
    sheet.append([1, "外套", "女童防晒衣", 1000, 5, 30000, 600])
    buffer = BytesIO()
    workbook.save(buffer)
    return buffer.getvalue()


def login(base: str) -> dict:
    response = requests.post(
        base + "/auth/login",
        json={
            "email": env_value("SMOKE_EMAIL", env_value("ADMIN_EMAIL", "admin@example.com")),
            "password": env_value("SMOKE_PASSWORD", env_value("ADMIN_PASSWORD", "change_me_admin_password")),
        },
        timeout=10,
    )
    response.raise_for_status()
    payload = response.json()
    workspace_id = payload["user"]["workspaces"][0]["id"]
    return {
        "Authorization": f"Bearer {payload['access_token']}",
        "X-Workspace-Id": str(workspace_id),
    }


def wait_batch(base: str, headers: dict, batch_no: str, timeout_seconds: int = 120) -> dict:
    deadline = time.time() + timeout_seconds
    while time.time() < deadline:
        response = requests.get(f"{base}/copy-batches/{batch_no}", headers=headers, timeout=10)
        response.raise_for_status()
        detail = response.json()
        if detail["batch"]["status"] in {"completed", "completed_with_errors", "canceled"}:
            return detail
        time.sleep(2)
    raise TimeoutError(f"batch did not finish: {batch_no}")


def ensure_mock_llm(base: str, headers: dict) -> dict:
    configs_response = requests.get(base + "/llm/configs", headers=headers, timeout=10)
    configs_response.raise_for_status()
    configs = configs_response.json()
    for config in configs:
        if config.get("provider") == "mock":
            activated_response = requests.post(f"{base}/llm/configs/{config['id']}/activate", headers=headers, timeout=10)
            activated_response.raise_for_status()
            return activated_response.json()
    created_response = requests.post(
        base + "/llm/configs",
        headers=headers,
        json={
            "provider": "mock",
            "display_name": "Smoke Mock",
            "model": "mock",
            "enabled": True,
            "updated_by": "smoke",
        },
        timeout=10,
    )
    created_response.raise_for_status()
    return created_response.json()


def main() -> int:
    base = sys.argv[1] if len(sys.argv) > 1 else "http://127.0.0.1:8000/api"
    for _ in range(20):
        try:
            requests.get(base + "/health", timeout=2).raise_for_status()
            break
        except requests.RequestException:
            time.sleep(1)
    out: dict[str, object] = {}
    out["health"] = requests.get(base + "/health", timeout=10).json()["status"]
    headers = login(base)
    out["login"] = "ok"
    out["activatedLlm"] = ensure_mock_llm(base, headers)["provider"]
    if out["activatedLlm"] != "mock":
        raise AssertionError("mock llm activation failed")
    out["llm"] = requests.get(base + "/llm/status", headers=headers, timeout=10).json()["provider"]

    config_response = requests.get(base + "/hot-search/config", headers=headers, timeout=10)
    config_response.raise_for_status()
    out["hotSearchDefaultBefore"] = config_response.json()["enabled_by_default"]
    reset_config_response = requests.put(
        base + "/hot-search/config",
        headers=headers,
        json={"enabled_by_default": False, "updated_by": "smoke"},
        timeout=10,
    )
    reset_config_response.raise_for_status()
    out["hotSearchDefaultReset"] = reset_config_response.json()["enabled_by_default"]
    if out["hotSearchDefaultReset"] is not False:
        raise AssertionError("hot search default reset failed")

    hot_import_response = requests.post(
        base + "/hot-search/import",
        headers=headers,
        files={
            "file": (
                "hot-search-smoke.xlsx",
                hot_search_workbook(),
                "application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
            )
        },
        timeout=10,
    )
    hot_import_response.raise_for_status()
    out["hotSearchImported"] = hot_import_response.json()["imported_count"]
    if out["hotSearchImported"] < 1:
        raise AssertionError("hot search import did not save any term")

    product = {
        "style_no": "A101",
        "product_no": "P101",
        "category_3": "外套",
        "category_4": "防晒衣",
        "age_range": "中大童",
        "gender": "女童",
        "season": "夏季",
        "scene": "出游",
        "fba": "清凉防晒，透气不闷，轻薄好穿",
        "remark": "冒烟测试",
        "created_by": "smoke",
        "updated_by": "smoke",
        "status": "draft",
        "skus": [{"sku_no": "SKC101", "color_name": "浅蓝", "color_code": "BL", "image_url": "", "color_remark": "清爽色"}],
    }
    created_response = requests.post(base + "/products", headers=headers, json=product, timeout=10)
    created_response.raise_for_status()
    created = created_response.json()
    out["productId"] = created["id"]

    batch_response = requests.post(f"{base}/products/{created['id']}/generate-copy-job", headers=headers, timeout=10)
    batch_response.raise_for_status()
    batch = batch_response.json()
    out["singleBatchNo"] = batch["batch_no"]
    detail = wait_batch(base, headers, batch["batch_no"])
    if detail["batch"]["success_count"] != 1:
        raise AssertionError("single generate job did not finish successfully")
    copy = requests.get(f"{base}/products/{created['id']}", headers=headers, timeout=10).json()["copy_output"]
    out["generatedTitleLength"] = len(copy["title"])

    hot_copy_response = requests.post(
        f"{base}/products/{created['id']}/generate-copy-job",
        headers=headers,
        json={"use_hot_search": True},
        timeout=10,
    )
    hot_copy_response.raise_for_status()
    hot_batch = hot_copy_response.json()
    hot_detail = wait_batch(base, headers, hot_batch["batch_no"])
    out["hotBatchStatus"] = hot_detail["batch"]["status"]
    if hot_detail["batch"]["success_count"] != 1:
        raise AssertionError("hot search generate job did not finish successfully")
    hot_copy = requests.get(f"{base}/products/{created['id']}", headers=headers, timeout=10).json()["copy_output"]

    validation_response = requests.post(
        f"{base}/products/{created['id']}/validate-copy",
        json={
            "title": hot_copy["title"],
            "main_image_tags": hot_copy["main_image_tags"],
            "color_copy": hot_copy["color_copy"],
            "operator_name": "smoke",
        },
        headers=headers,
        timeout=10,
    )
    validation_response.raise_for_status()
    out["validationPassed"] = validation_response.json()["passed"]
    if out["validationPassed"] is not True:
        raise AssertionError("generated copy did not pass validation")

    save_response = requests.put(
        f"{base}/products/{created['id']}/copy",
        headers=headers,
        json={
            "title": hot_copy["title"],
            "main_image_tags": hot_copy["main_image_tags"],
            "color_copy": "夏日百搭",
            "operator_name": "smoke",
            "change_reason": "冒烟人工优化",
        },
        timeout=10,
    )
    save_response.raise_for_status()
    out["savedColorCopy"] = save_response.json()["color_copy"]

    versions = requests.get(f"{base}/products/{created['id']}/copy-versions", headers=headers, timeout=10).json()
    out["versionCount"] = len(versions)

    history_response = requests.post(
        f"{base}/products/{created['id']}/save-history-case",
        headers=headers,
        json={"reason": "冒烟优秀案例", "operator_name": "smoke"},
        timeout=10,
    )
    history_response.raise_for_status()
    out["historyId"] = history_response.json()["id"]

    report_response = requests.post(base + "/learning/analyze", headers=headers, timeout=10)
    report_response.raise_for_status()
    out["learningSampleCount"] = report_response.json()["sample_count"]

    export_response = requests.get(base + "/excel/export", headers=headers, timeout=10)
    export_response.raise_for_status()
    out["exportId"] = export_response.json()["export_id"]

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
