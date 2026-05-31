import os

from .base import LlmClient
from .mock_client import MockClient
from .openai_compatible_client import OpenAICompatibleClient


class DisabledClient(LlmClient):
    provider = "disabled"
    model = "disabled"

    def generate_json(self, messages: list[dict], schema_hint: dict | None = None) -> dict:
        raise RuntimeError("LLM_PROVIDER=disabled，文案生成已禁用，请配置模型或切换mock模式")


def get_llm_client() -> LlmClient:
    provider = os.getenv("LLM_PROVIDER", "mock").strip() or "mock"
    if provider == "mock":
        return MockClient()
    if provider == "openai_compatible":
        return OpenAICompatibleClient()
    if provider == "disabled":
        return DisabledClient()
    raise RuntimeError(f"未知LLM_PROVIDER：{provider}")


def get_llm_status() -> dict:
    provider = os.getenv("LLM_PROVIDER", "mock").strip() or "mock"
    model = os.getenv("LLM_MODEL", "mock")
    if provider == "openai_compatible":
        enabled = bool(os.getenv("LLM_API_KEY") and os.getenv("LLM_BASE_URL") and model)
        message = "openai-compatible configured" if enabled else "openai-compatible missing configuration"
        return {"provider": provider, "model": model, "enabled": enabled, "message": message}
    if provider == "disabled":
        return {"provider": provider, "model": model, "enabled": False, "message": "generation disabled"}
    return {"provider": "mock", "model": "mock", "enabled": True, "message": "mock mode enabled"}
