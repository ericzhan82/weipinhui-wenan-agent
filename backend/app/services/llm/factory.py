import os

from sqlalchemy.orm import Session

from app.models import LlmConfig

from .base import LlmClient
from .mock_client import MockClient
from .openai_compatible_client import OpenAICompatibleClient


class DisabledClient(LlmClient):
    provider = "disabled"
    model = "disabled"

    def generate_json(self, messages: list[dict], schema_hint: dict | None = None) -> dict:
        raise RuntimeError("LLM_PROVIDER=disabled，文案生成已禁用，请配置模型或切换mock模式")


def get_active_llm_config(db: Session | None = None) -> LlmConfig | None:
    if db is None:
        return None
    return (
        db.query(LlmConfig)
        .filter(LlmConfig.enabled.is_(True))
        .order_by(LlmConfig.updated_at.desc(), LlmConfig.id.desc())
        .first()
    )


def get_llm_client(db: Session | None = None) -> LlmClient:
    config = get_active_llm_config(db)
    if config:
        provider = config.provider.strip() or "mock"
        if provider == "mock":
            return MockClient()
        if provider == "disabled":
            return DisabledClient()
        return OpenAICompatibleClient(
            provider=provider,
            api_key=config.api_key or "",
            base_url=config.base_url or "",
            model=config.model,
            timeout_seconds=config.timeout_seconds,
            temperature=config.temperature,
            max_retries=config.max_retries,
        )

    provider = os.getenv("LLM_PROVIDER", "mock").strip() or "mock"
    if provider == "mock":
        return MockClient()
    if provider == "openai_compatible":
        return OpenAICompatibleClient()
    if provider == "disabled":
        return DisabledClient()
    raise RuntimeError(f"未知LLM_PROVIDER：{provider}")


def get_llm_status(db: Session | None = None) -> dict:
    config = get_active_llm_config(db)
    if config:
        provider = config.provider.strip() or "mock"
        if provider == "mock":
            return {
                "source": "database",
                "config_id": config.id,
                "provider": "mock",
                "display_name": config.display_name,
                "model": "mock",
                "enabled": True,
                "api_key_set": False,
                "base_url": config.base_url,
                "message": "mock mode enabled from database",
            }
        if provider == "disabled":
            return {
                "source": "database",
                "config_id": config.id,
                "provider": "disabled",
                "display_name": config.display_name,
                "model": config.model,
                "enabled": False,
                "api_key_set": bool(config.api_key),
                "base_url": config.base_url,
                "message": "generation disabled from database",
            }
        ready = bool(config.api_key and config.base_url and config.model)
        return {
            "source": "database",
            "config_id": config.id,
            "provider": provider,
            "display_name": config.display_name,
            "model": config.model,
            "enabled": ready,
            "api_key_set": bool(config.api_key),
            "base_url": config.base_url,
            "message": "database model configured" if ready else "database model missing api key, base url or model",
        }

    provider = os.getenv("LLM_PROVIDER", "mock").strip() or "mock"
    model = os.getenv("LLM_MODEL", "mock")
    if provider == "openai_compatible":
        enabled = bool(os.getenv("LLM_API_KEY") and os.getenv("LLM_BASE_URL") and model)
        message = "openai-compatible configured" if enabled else "openai-compatible missing configuration"
        return {
            "source": "environment",
            "provider": provider,
            "model": model,
            "enabled": enabled,
            "api_key_set": bool(os.getenv("LLM_API_KEY")),
            "base_url": os.getenv("LLM_BASE_URL", ""),
            "message": message,
        }
    if provider == "disabled":
        return {
            "source": "environment",
            "provider": provider,
            "model": model,
            "enabled": False,
            "api_key_set": bool(os.getenv("LLM_API_KEY")),
            "base_url": os.getenv("LLM_BASE_URL", ""),
            "message": "generation disabled",
        }
    return {
        "source": "environment",
        "provider": "mock",
        "model": "mock",
        "enabled": True,
        "api_key_set": False,
        "base_url": "",
        "message": "mock mode enabled",
    }
