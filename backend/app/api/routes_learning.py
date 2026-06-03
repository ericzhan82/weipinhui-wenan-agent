from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_workspace_context, require_workspace_write
from app.db import get_db
from app.models import LearningReport, RuleSuggestion
from app.schemas import SuggestionReviewRequest
from app.services.learning_service import accept_suggestion, analyze_learning, learning_summary, reject_suggestion

router = APIRouter(prefix="/api/learning", tags=["learning"])


@router.get("/summary")
def summary(context: AuthContext = Depends(get_workspace_context), db: Session = Depends(get_db)):
    return learning_summary(db, context.workspace_id)


@router.post("/analyze")
def analyze(context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    return analyze_learning(db, context.workspace_id)


@router.get("/reports")
def reports(context: AuthContext = Depends(get_workspace_context), db: Session = Depends(get_db)):
    return db.query(LearningReport).filter(LearningReport.workspace_id == context.workspace_id).order_by(LearningReport.created_at.desc()).all()


@router.get("/suggestions")
def suggestions(context: AuthContext = Depends(get_workspace_context), db: Session = Depends(get_db)):
    return db.query(RuleSuggestion).filter(RuleSuggestion.workspace_id == context.workspace_id).order_by(RuleSuggestion.created_at.desc()).all()


@router.post("/suggestions/{suggestion_id}/accept")
def accept(suggestion_id: int, payload: SuggestionReviewRequest, context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    try:
        return accept_suggestion(db, suggestion_id, context.operator_name, context.workspace_id)
    except ValueError as exc:
        raise HTTPException(404, detail=str(exc)) from exc


@router.post("/suggestions/{suggestion_id}/reject")
def reject(suggestion_id: int, payload: SuggestionReviewRequest, context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    try:
        return reject_suggestion(db, suggestion_id, context.operator_name, context.workspace_id)
    except ValueError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
