from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import LlmConfig
from app.schemas import LlmConfigCreate, LlmConfigRead, LlmConfigUpdate
from app.services.llm import get_llm_status

router = APIRouter(prefix="/api/llm", tags=["llm"])


@router.get("/status")
def llm_status(db: Session = Depends(get_db)) -> dict:
    return get_llm_status(db)


def _read_config(config: LlmConfig) -> LlmConfigRead:
    return LlmConfigRead(
        id=config.id,
        provider=config.provider,
        display_name=config.display_name,
        base_url=config.base_url,
        model=config.model,
        temperature=config.temperature,
        timeout_seconds=config.timeout_seconds,
        max_retries=config.max_retries,
        enabled=config.enabled,
        updated_by=config.updated_by,
        api_key_set=bool(config.api_key),
        created_at=config.created_at,
        updated_at=config.updated_at,
    )


def _disable_other_configs(db: Session, active_id: int | None = None) -> None:
    query = db.query(LlmConfig).filter(LlmConfig.enabled.is_(True))
    if active_id is not None:
        query = query.filter(LlmConfig.id != active_id)
    for config in query.all():
        config.enabled = False


@router.get("/configs", response_model=list[LlmConfigRead])
def list_llm_configs(db: Session = Depends(get_db)) -> list[LlmConfigRead]:
    configs = db.query(LlmConfig).order_by(LlmConfig.enabled.desc(), LlmConfig.updated_at.desc()).all()
    return [_read_config(config) for config in configs]


@router.post("/configs", response_model=LlmConfigRead)
def create_llm_config(payload: LlmConfigCreate, db: Session = Depends(get_db)) -> LlmConfigRead:
    if payload.enabled:
        _disable_other_configs(db)
    config = LlmConfig(**payload.model_dump(exclude={"api_key"}), api_key=payload.api_key or None)
    db.add(config)
    db.commit()
    db.refresh(config)
    return _read_config(config)


@router.put("/configs/{config_id}", response_model=LlmConfigRead)
def update_llm_config(config_id: int, payload: LlmConfigUpdate, db: Session = Depends(get_db)) -> LlmConfigRead:
    config = db.get(LlmConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    values = payload.model_dump(exclude_unset=True)
    api_key = values.pop("api_key", None)
    for key, value in values.items():
        setattr(config, key, value)
    if api_key and api_key.strip():
        config.api_key = api_key.strip()
    if config.enabled:
        _disable_other_configs(db, active_id=config.id)
    db.commit()
    db.refresh(config)
    return _read_config(config)


@router.post("/configs/{config_id}/activate", response_model=LlmConfigRead)
def activate_llm_config(config_id: int, db: Session = Depends(get_db)) -> LlmConfigRead:
    config = db.get(LlmConfig, config_id)
    if not config:
        raise HTTPException(status_code=404, detail="模型配置不存在")
    _disable_other_configs(db, active_id=config.id)
    config.enabled = True
    db.commit()
    db.refresh(config)
    return _read_config(config)
