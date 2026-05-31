from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Rule
from app.schemas import RuleCreate, RuleRead, RuleUpdate

router = APIRouter(prefix="/api/rules", tags=["rules"])


@router.get("", response_model=list[RuleRead])
def list_rules(db: Session = Depends(get_db)):
    return db.query(Rule).order_by(Rule.rule_type, Rule.id).all()


@router.get("/{rule_id}", response_model=RuleRead)
def get_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(Rule, rule_id)
    if not rule:
        raise HTTPException(404, "规则不存在")
    return rule


@router.post("", response_model=RuleRead)
def create_rule(payload: RuleCreate, db: Session = Depends(get_db)):
    rule = Rule(**payload.model_dump())
    db.add(rule)
    db.commit()
    db.refresh(rule)
    return rule


@router.put("/{rule_id}", response_model=RuleRead)
def update_rule(rule_id: int, payload: RuleUpdate, db: Session = Depends(get_db)):
    rule = db.get(Rule, rule_id)
    if not rule:
        raise HTTPException(404, "规则不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(rule, key, value)
    db.commit()
    db.refresh(rule)
    return rule


@router.delete("/{rule_id}")
def disable_rule(rule_id: int, db: Session = Depends(get_db)):
    rule = db.get(Rule, rule_id)
    if not rule:
        raise HTTPException(404, "规则不存在")
    rule.enabled = False
    db.commit()
    return {"disabled": True}
