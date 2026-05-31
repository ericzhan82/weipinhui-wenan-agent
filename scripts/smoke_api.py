import json
import sys
import time

import requests


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
    out["llm"] = requests.get(base + "/llm/status", timeout=10).json()["provider"]
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
    created_response = requests.post(base + "/products", json=product, timeout=10)
    created_response.raise_for_status()
    created = created_response.json()
    out["productId"] = created["id"]

    copy_response = requests.post(f"{base}/products/{created['id']}/generate-copy", timeout=10)
    copy_response.raise_for_status()
    copy = copy_response.json()
    out["generatedTitleLength"] = len(copy["title"])

    validation_response = requests.post(
        f"{base}/products/{created['id']}/validate-copy",
        json={
            "title": copy["title"],
            "main_image_tags": copy["main_image_tags"],
            "color_copy": copy["color_copy"],
            "operator_name": "smoke",
        },
        timeout=10,
    )
    validation_response.raise_for_status()
    out["validationPassed"] = validation_response.json()["passed"]

    save_response = requests.put(
        f"{base}/products/{created['id']}/copy",
        json={
            "title": copy["title"],
            "main_image_tags": copy["main_image_tags"],
            "color_copy": "夏日百搭",
            "operator_name": "smoke",
            "change_reason": "冒烟人工优化",
        },
        timeout=10,
    )
    save_response.raise_for_status()
    out["savedColorCopy"] = save_response.json()["color_copy"]

    versions = requests.get(f"{base}/products/{created['id']}/copy-versions", timeout=10).json()
    out["versionCount"] = len(versions)

    history_response = requests.post(
        f"{base}/products/{created['id']}/save-history-case",
        json={"reason": "冒烟优秀案例", "operator_name": "smoke"},
        timeout=10,
    )
    history_response.raise_for_status()
    out["historyId"] = history_response.json()["id"]

    report_response = requests.post(base + "/learning/analyze", timeout=10)
    report_response.raise_for_status()
    out["learningSampleCount"] = report_response.json()["sample_count"]

    export_response = requests.get(base + "/excel/export", timeout=10)
    export_response.raise_for_status()
    out["exportId"] = export_response.json()["export_id"]

    print(json.dumps(out, ensure_ascii=False, indent=2))
    return 0


if __name__ == "__main__":
    raise SystemExit(main())
