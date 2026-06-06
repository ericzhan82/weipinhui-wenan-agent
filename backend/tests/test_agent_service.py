from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import AgentRun, Product, Workspace
from app.services.agent_service import (
    AGENT_MODE_BUSINESS,
    AGENT_MODE_LEGACY,
    get_agent_config,
    resolve_agent_mode,
    set_agent_config,
)
from app.services.copy_generator import generate_copy_for_product


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_agent_config_defaults_to_legacy_off():
    db = _session()
    config = get_agent_config(db, workspace_id=1)

    assert config["enabled_by_default"] is False
    assert config["default_agent_mode"] == AGENT_MODE_LEGACY
    assert resolve_agent_mode(db, workspace_id=1, requested_mode=None) == AGENT_MODE_LEGACY


def test_agent_config_can_enable_business_agent_by_default():
    db = _session()

    set_agent_config(
        db,
        workspace_id=1,
        enabled_by_default=True,
        default_agent_mode=AGENT_MODE_BUSINESS,
        updated_by="tester",
    )

    assert resolve_agent_mode(db, workspace_id=1, requested_mode=None) == AGENT_MODE_BUSINESS
    assert resolve_agent_mode(db, workspace_id=1, requested_mode=AGENT_MODE_LEGACY) == AGENT_MODE_LEGACY


def test_business_agent_generation_records_steps(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_MODEL", "mock")
    db = _session()
    workspace = Workspace(name="Default", slug="default")
    db.add(workspace)
    db.flush()
    product = Product(
        workspace_id=workspace.id,
        style_no="A100",
        product_no="P100",
        category_3="童装",
        category_4="T恤",
        age_range="中童",
        gender="女童",
        season="夏",
        scene="校园",
        fba="柔软透气，适合夏季日常穿着",
    )
    db.add(product)
    db.commit()

    payload = generate_copy_for_product(
        db,
        product.id,
        operator_name="tester",
        agent_mode=AGENT_MODE_BUSINESS,
    )

    run = db.query(AgentRun).filter(AgentRun.product_id == product.id).one()
    assert payload["agent_mode"] == AGENT_MODE_BUSINESS
    assert payload["agent_run_id"] == run.id
    assert run.status == "success"
    assert [step["skill_key"] for step in payload["agent_steps"]] == [
        "context_inspector",
        "rule_retriever",
        "hot_search_selector",
        "copy_writer",
        "copy_validator",
        "learning_suggestion_builder",
    ]

