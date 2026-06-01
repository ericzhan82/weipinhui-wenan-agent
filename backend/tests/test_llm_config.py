from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.api.routes_llm import activate_llm_config, create_llm_config, list_llm_configs
from app.models import LlmConfig
from app.schemas import LlmConfigCreate
from app.services.llm.factory import get_llm_client, get_llm_status


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_database_llm_config_overrides_environment(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    db = _session()
    db.add(
        LlmConfig(
            provider="deepseek",
            display_name="DeepSeek",
            api_key="db-secret",
            base_url="https://api.deepseek.com/v1",
            model="deepseek-chat",
            temperature=0.2,
            timeout_seconds=45,
            max_retries=2,
            enabled=True,
        )
    )
    db.commit()

    client = get_llm_client(db)

    assert client.provider == "deepseek"
    assert client.model == "deepseek-chat"
    assert client.api_key == "db-secret"
    assert client.base_url == "https://api.deepseek.com/v1"
    assert client.max_retries == 2


def test_llm_status_masks_database_api_key():
    db = _session()
    db.add(
        LlmConfig(
            provider="qwen",
            display_name="通义千问",
            api_key="should-not-leak",
            base_url="https://dashscope.aliyuncs.com/compatible-mode/v1",
            model="qwen-plus",
            enabled=True,
        )
    )
    db.commit()

    status = get_llm_status(db)

    assert status["source"] == "database"
    assert status["provider"] == "qwen"
    assert status["api_key_set"] is True
    assert "api_key" not in status
    assert "should-not-leak" not in str(status)


def test_llm_config_routes_create_list_and_activate_without_key_leak():
    db = _session()

    first = create_llm_config(
        LlmConfigCreate(
            provider="deepseek",
            display_name="DeepSeek",
            api_key="route-secret",
            base_url="https://api.deepseek.com/v1",
            model="deepseek-chat",
            enabled=True,
        ),
        db,
    )
    second = create_llm_config(
        LlmConfigCreate(
            provider="mock",
            display_name="Mock",
            model="mock",
            enabled=False,
        ),
        db,
    )

    assert first.api_key_set is True
    assert not hasattr(first, "api_key")

    activated = activate_llm_config(second.id, db)
    configs = list_llm_configs(db)

    assert activated.enabled is True
    assert {config.id: config.enabled for config in configs} == {first.id: False, second.id: True}
    assert "route-secret" not in str(configs)
