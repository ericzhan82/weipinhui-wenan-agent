from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import LearningReport, RuleSuggestion
from app.schemas import SuggestionReviewRequest
from app.services.learning_service import accept_suggestion, analyze_learning, learning_summary, reject_suggestion

router = APIRouter(prefix="/api/learning", tags=["learning"])


@router.get("/summary")
def summary(db: Session = Depends(get_db)):
    return learning_summary(db)


@router.post("/analyze")
def analyze(db: Session = Depends(get_db)):
    return analyze_learning(db)


@router.get("/reports")
def reports(db: Session = Depends(get_db)):
    return db.query(LearningReport).order_by(LearningReport.created_at.desc()).all()


@router.get("/suggestions")
def suggestions(db: Session = Depends(get_db)):
    return db.query(RuleSuggestion).order_by(RuleSuggestion.created_at.desc()).all()


@router.post("/suggestions/{suggestion_id}/accept")
def accept(suggestion_id: int, payload: SuggestionReviewRequest, db: Session = Depends(get_db)):
    try:
        return accept_suggestion(db, suggestion_id, payload.reviewer)
    except ValueError as exc:
        raise HTTPException(404, detail=str(exc)) from exc


@router.post("/suggestions/{suggestion_id}/reject")
def reject(suggestion_id: int, payload: SuggestionReviewRequest, db: Session = Depends(get_db)):
    try:
        return reject_suggestion(db, suggestion_id, payload.reviewer)
    except ValueError as exc:
        raise HTTPException(404, detail=str(exc)) from exc
