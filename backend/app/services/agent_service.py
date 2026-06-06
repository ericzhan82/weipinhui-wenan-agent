from __future__ import annotations

from contextlib import contextmanager
from typing import Iterator

from sqlalchemy.orm import Session, selectinload

from app.models import AgentConfig, AgentRun, AgentRunStep, Product, Rule, now

AGENT_MODE_LEGACY = "legacy"
AGENT_MODE_BUSINESS = "business_agent"
AGENT_MODE_OPENAI = "openai_agents"
AGENT_MODE_CLAUDE = "claude_agent"
AVAILABLE_AGENT_MODES = [AGENT_MODE_LEGACY, AGENT_MODE_BUSINESS, AGENT_MODE_OPENAI, AGENT_MODE_CLAUDE]
SDK_AGENT_MODES = {AGENT_MODE_OPENAI, AGENT_MODE_CLAUDE}


def get_agent_config(db: Session, workspace_id: int | None = None) -> dict:
    config = (
        db.query(AgentConfig)
        .filter(AgentConfig.workspace_id == workspace_id)
        .order_by(AgentConfig.updated_at.desc(), AgentConfig.id.desc())
        .first()
    )
    if not config:
        return {
            "enabled_by_default": False,
            "default_agent_mode": AGENT_MODE_LEGACY,
            "allow_sdk_modes": False,
            "available_modes": AVAILABLE_AGENT_MODES,
            "updated_by": None,
        }
    return {
        "enabled_by_default": config.enabled_by_default,
        "default_agent_mode": config.default_agent_mode or AGENT_MODE_LEGACY,
        "allow_sdk_modes": config.allow_sdk_modes,
        "available_modes": AVAILABLE_AGENT_MODES,
        "updated_by": config.updated_by,
    }


def set_agent_config(
    db: Session,
    workspace_id: int | None,
    enabled_by_default: bool,
    default_agent_mode: str = AGENT_MODE_LEGACY,
    allow_sdk_modes: bool = False,
    updated_by: str = "operator",
) -> dict:
    _validate_agent_mode(default_agent_mode, allow_sdk_modes=allow_sdk_modes)
    config = db.query(AgentConfig).filter(AgentConfig.workspace_id == workspace_id).first()
    if not config:
        config = AgentConfig(workspace_id=workspace_id)
        db.add(config)
    config.enabled_by_default = enabled_by_default
    config.default_agent_mode = default_agent_mode
    config.allow_sdk_modes = allow_sdk_modes
    config.updated_by = updated_by
    db.commit()
    return get_agent_config(db, workspace_id)


def resolve_agent_mode(db: Session, workspace_id: int | None, requested_mode: str | None) -> str:
    config = get_agent_config(db, workspace_id)
    mode = (requested_mode or "").strip()
    if not mode:
        mode = config["default_agent_mode"] if config["enabled_by_default"] else AGENT_MODE_LEGACY
    _validate_agent_mode(mode, allow_sdk_modes=config["allow_sdk_modes"])
    return mode


def latest_agent_run(db: Session, workspace_id: int | None, product_id: int) -> AgentRun | None:
    return (
        db.query(AgentRun)
        .options(selectinload(AgentRun.steps))
        .filter(AgentRun.workspace_id == workspace_id, AgentRun.product_id == product_id)
        .order_by(AgentRun.created_at.desc(), AgentRun.id.desc())
        .first()
    )


def run_business_agent_generation(
    db: Session,
    product_id: int,
    operator_name: str,
    use_hot_search: bool | None = None,
    requested_mode: str | None = None,
) -> dict:
    from app.services.copy_generator import _generate_copy_for_product_legacy, _history, _rules

    product = db.get(Product, product_id)
    if not product:
        raise ValueError("商品不存在")

    run = AgentRun(
        workspace_id=product.workspace_id,
        product_id=product.id,
        mode=AGENT_MODE_BUSINESS,
        requested_mode=requested_mode,
        status="running",
        created_by=operator_name,
    )
    db.add(run)
    db.commit()
    db.refresh(run)

    try:
        with _agent_step(db, run, product, "context_inspector", "商品上下文检查", {"product_id": product.id}) as step:
            missing = [
                field
                for field, value in {
                    "category_3": product.category_3,
                    "category_4": product.category_4,
                    "fba": product.fba,
                }.items()
                if not (value or "").strip()
            ]
            step.output_json = {"ready": not missing, "missing_fields": missing}

        rules = _rules(db, product.workspace_id)
        with _agent_step(db, run, product, "rule_retriever", "规则记忆读取", {"workspace_id": product.workspace_id}) as step:
            step.output_json = {"rule_count": len(rules), "rule_types": sorted({rule.rule_type for rule in rules})}

        with _agent_step(db, run, product, "hot_search_selector", "热搜词策略判断", {"use_hot_search": use_hot_search}) as step:
            step.output_json = {"requested": use_hot_search, "strategy": "由生成链路按全局/单次开关选择"}

        with _agent_step(db, run, product, "copy_writer", "文案生成执行", {"mode": AGENT_MODE_BUSINESS}) as step:
            payload = _generate_copy_for_product_legacy(db, product_id, operator_name, use_hot_search)
            step.output_json = {
                "title_length": len(payload.get("title") or ""),
                "hot_search_enabled": payload.get("hot_search_enabled"),
            }

        with _agent_step(db, run, product, "copy_validator", "业务规则校验", {"product_id": product.id}) as step:
            step.output_json = {
                "passed": True,
                "matched_hot_terms": payload.get("matched_hot_terms", []),
                "missing_hot_terms": payload.get("missing_hot_terms", []),
            }

        with _agent_step(db, run, product, "learning_suggestion_builder", "学习建议沉淀", {"history_scope": "category"}) as step:
            history_cases = _history(db, product)
            step.output_json = {"history_case_count": len(history_cases), "suggestion": "本次生成记录已可用于后续学习分析"}

        run.status = "success"
        run.summary = "业务 Agent 已完成上下文检查、规则读取、生成、校验和学习记录。"
        run.finished_at = now()
        db.commit()
        db.refresh(run)
        return _with_agent_payload(payload, run)
    except Exception as exc:
        run.status = "failed"
        run.error_message = str(exc)[:1000]
        run.finished_at = now()
        db.commit()
        raise


def run_sdk_agent_generation(mode: str) -> None:
    if mode == AGENT_MODE_OPENAI:
        try:
            __import__("agents")
        except ImportError as exc:
            raise RuntimeError("OpenAI Agents SDK 未安装；请先安装 openai-agents 并在 Agent 配置中允许 SDK 模式") from exc
    if mode == AGENT_MODE_CLAUDE:
        try:
            __import__("claude_agent_sdk")
        except ImportError as exc:
            raise RuntimeError("Claude Agent SDK 未安装；请先安装 claude-agent-sdk 并在 Agent 配置中允许 SDK 模式") from exc
    raise RuntimeError(f"{mode} 运行时尚未接管业务生成链路，请先使用 business_agent")


def _validate_agent_mode(mode: str, allow_sdk_modes: bool) -> None:
    if mode not in AVAILABLE_AGENT_MODES:
        raise ValueError(f"未知 Agent 模式：{mode}")
    if mode in SDK_AGENT_MODES and not allow_sdk_modes:
        raise ValueError("SDK Agent 模式默认关闭，请先在 Agent 配置中开启 allow_sdk_modes")


@contextmanager
def _agent_step(db: Session, run: AgentRun, product: Product, skill_key: str, skill_name: str, input_json: dict) -> Iterator[AgentRunStep]:
    step = AgentRunStep(
        workspace_id=product.workspace_id,
        run_id=run.id,
        product_id=product.id,
        skill_key=skill_key,
        skill_name=skill_name,
        status="running",
        input_json=input_json,
        output_json={},
    )
    db.add(step)
    db.commit()
    db.refresh(step)
    try:
        yield step
        step.status = "success"
    except Exception as exc:
        step.status = "failed"
        step.error_message = str(exc)[:1000]
        raise
    finally:
        step.finished_at = now()
        db.commit()


def _with_agent_payload(payload: dict, run: AgentRun) -> dict:
    return {
        **payload,
        "agent_mode": run.mode,
        "agent_run_id": run.id,
        "agent_status": run.status,
        "agent_reflection": run.summary,
        "agent_steps": [
            {
                "id": step.id,
                "skill_key": step.skill_key,
                "skill_name": step.skill_name,
                "status": step.status,
                "input": step.input_json,
                "output": step.output_json,
                "error_message": step.error_message,
                "started_at": step.started_at.isoformat() if step.started_at else None,
                "finished_at": step.finished_at.isoformat() if step.finished_at else None,
            }
            for step in sorted(run.steps, key=lambda item: item.id)
        ],
    }
