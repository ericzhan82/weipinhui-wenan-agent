from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_workspace_context, require_workspace_write
from app.db import get_db
from app.models import HistoryCase
from app.schemas import HistoryCaseCreate
from app.services.history_service import save_history_case

router = APIRouter(prefix="/api", tags=["history"])


@router.get("/history-cases")
def list_history_cases(
    style_no: str | None = None,
    category_3: str | None = None,
    category_4: str | None = None,
    gender: str | None = None,
    season: str | None = None,
    scene: str | None = None,
    keyword: str | None = Query(default=None),
    context: AuthContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
):
    query = db.query(HistoryCase).filter(HistoryCase.workspace_id == context.workspace_id)
    filters = {
        HistoryCase.style_no: style_no,
        HistoryCase.category_3: category_3,
        HistoryCase.category_4: category_4,
        HistoryCase.gender: gender,
        HistoryCase.season: season,
        HistoryCase.scene: scene,
    }
    for column, value in filters.items():
        if value:
            query = query.filter(column == value)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                HistoryCase.title.like(like),
                HistoryCase.color_copy.like(like),
                HistoryCase.fba.like(like),
                HistoryCase.reason.like(like),
            )
        )
    return query.order_by(HistoryCase.created_at.desc()).all()


@router.post("/products/{product_id}/save-history-case")
def create_history_case(product_id: int, payload: HistoryCaseCreate, context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    try:
        return save_history_case(db, product_id, payload.reason, context.operator_name, context.workspace_id)
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc
