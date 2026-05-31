import re

from .base import LlmClient


def _clean(text: str | None) -> str:
    return re.sub(r"[\s，。；;、,]+", "", text or "")


def _core_from_fba(fba: str | None) -> str:
    text = fba or ""
    if "防晒" in text:
        return "清凉防晒"
    if "透气" in text:
        return "舒适透气"
    if "柔软" in text or "亲肤" in text:
        return "柔软亲肤"
    return (_clean(text)[:4] or "舒适百搭")


def build_mock_title(product: dict) -> str:
    core = _core_from_fba(product.get("fba"))
    parts = [
        core,
        _clean(product.get("age_range")),
        _clean(product.get("gender")),
        _clean(product.get("category_4") or product.get("category_3")),
        _clean(product.get("season")),
        _clean(product.get("scene")),
        "轻薄舒适外套",
    ]
    title = "".join(parts)
    filler = "百搭好穿清爽自在日常通勤活力"
    while len(title) < 29:
        title += filler[(len(title) - len("".join(parts))) % len(filler)]
    return title[:30] if len(title) > 30 else title


class MockClient(LlmClient):
    provider = "mock"
    model = "mock"

    def generate_json(self, messages: list[dict], schema_hint: dict | None = None) -> dict:
        product = (schema_hint or {}).get("product", {})
        return {
            "title": build_mock_title(product),
            "main_image_tags": ["清凉防晒", "透气不闷", "出游好穿"],
            "color_copy": "清爽显白",
            "source_basis": "mock模式根据FBA、品类、季节和场景生成，可用于本地演示",
            "warnings": [],
        }
