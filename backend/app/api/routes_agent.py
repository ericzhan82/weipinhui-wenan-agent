from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_workspace_context, require_workspace_admin
from app.db import get_db
from app.models import Product
from app.schemas import AgentConfigRead, AgentConfigUpdate, AgentRunRead
from app.services.agent_service import get_agent_config, latest_agent_run, set_agent_config

router = APIRouter(prefix="/api", tags=["agent"])


@router.get("/agent/config", response_model=AgentConfigRead)
def read_agent_config(context: AuthContext = Depends(get_workspace_context), db: Session = Depends(get_db)):
    return get_agent_config(db, context.workspace_id)


@router.put("/agent/config", response_model=AgentConfigRead)
def update_agent_config(
    payload: AgentConfigUpdate,
    context: AuthContext = Depends(require_workspace_admin),
    db: Session = Depends(get_db),
):
    try:
        return set_agent_config(
            db,
            context.workspace_id,
            enabled_by_default=payload.enabled_by_default,
            default_agent_mode=payload.default_agent_mode,
            allow_sdk_modes=payload.allow_sdk_modes,
            updated_by=context.operator_name,
        )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc


@router.get("/products/{product_id}/agent-runs/latest", response_model=AgentRunRead | None)
def read_latest_agent_run(
    product_id: int,
    context: AuthContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
):
    product = db.get(Product, product_id)
    if not product or product.workspace_id != context.workspace_id:
        raise HTTPException(404, "商品不存在")
    return latest_agent_run(db, context.workspace_id, product_id)
