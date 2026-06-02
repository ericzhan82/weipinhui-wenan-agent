from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import CopyOutput, CopyVersion
from app.schemas import CopyGenerateRequest, CopyRead, CopySaveRequest, RewriteCopyRequest, ValidateCopyRequest
from app.services.copy_generator import (
    generate_copy_for_product,
    rewrite_copy_for_product,
    save_manual_copy,
    validate_product_copy,
)
from app.services.version_service import create_copy_version

router = APIRouter(prefix="/api/products", tags=["copies"])


@router.post("/{product_id}/generate-copy")
def generate_copy(product_id: int, payload: CopyGenerateRequest | None = None, db: Session = Depends(get_db)):
    try:
        return generate_copy_for_product(db, product_id, use_hot_search=payload.use_hot_search if payload else None)
    except ValueError as exc:
        raise HTTPException(400, detail=exc.args[0]) from exc
    except RuntimeError as exc:
        raise HTTPException(502, detail=str(exc)) from exc


@router.post("/{product_id}/rewrite-copy")
def rewrite_copy(product_id: int, payload: RewriteCopyRequest, db: Session = Depends(get_db)):
    try:
        return rewrite_copy_for_product(db, product_id, payload.rewrite_instruction, payload.operator_name)
    except ValueError as exc:
        raise HTTPException(400, detail=exc.args[0]) from exc
    except RuntimeError as exc:
        raise HTTPException(502, detail=str(exc)) from exc


@router.put("/{product_id}/copy", response_model=CopyRead)
def save_copy(product_id: int, payload: CopySaveRequest, db: Session = Depends(get_db)):
    try:
        return save_manual_copy(
            db,
            product_id,
            payload.title,
            payload.main_image_tags,
            payload.color_copy,
            payload.operator_name,
            payload.change_reason,
        )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc


@router.post("/{product_id}/validate-copy")
def validate_copy(product_id: int, payload: ValidateCopyRequest, db: Session = Depends(get_db)):
    try:
        return validate_product_copy(
            db,
            product_id,
            payload.title,
            payload.main_image_tags,
            payload.color_copy,
            payload.operator_name,
        )
    except ValueError as exc:
        raise HTTPException(400, detail=str(exc)) from exc


@router.get("/{product_id}/copy-versions")
def versions(product_id: int, db: Session = Depends(get_db)):
    return (
        db.query(CopyVersion)
        .filter(CopyVersion.product_id == product_id)
        .order_by(CopyVersion.version_no.desc())
        .all()
    )


@router.post("/{product_id}/copy-versions/{version_id}/restore", response_model=CopyRead)
def restore_version(product_id: int, version_id: int, db: Session = Depends(get_db)):
    version = db.get(CopyVersion, version_id)
    if not version or version.product_id != product_id:
        raise HTTPException(404, "版本不存在")
    output = db.query(CopyOutput).filter(CopyOutput.product_id == product_id).first()
    if not output:
        output = CopyOutput(product_id=product_id, created_by="restore")
        db.add(output)
        db.flush()
    output.title = version.title
    output.main_image_tags = version.main_image_tags
    output.color_copy = version.color_copy
    output.source_basis = "从历史版本恢复"
    output.status = "edited"
    output.updated_by = "restore"
    create_copy_version(
        db,
        product_id,
        output,
        "restore",
        output.title or "",
        output.main_image_tags,
        output.color_copy or "",
        "restore",
        f"恢复版本#{version.version_no}",
    )
    db.commit()
    db.refresh(output)
    return output
