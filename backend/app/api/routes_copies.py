from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_workspace_context, require_workspace_write
from app.db import get_db
from app.models import CopyOutput, CopyVersion, Product
from app.schemas import CopyBatchRead, CopyGenerateRequest, CopyRead, CopySaveRequest, RewriteCopyRequest, ValidateCopyRequest
from app.services.copy_batch_service import create_single_product_batch
from app.services.copy_generator import (
    generate_copy_for_product,
    rewrite_copy_for_product,
    save_manual_copy,
    validate_product_copy,
)
from app.services.version_service import create_copy_version

router = APIRouter(prefix="/api/products", tags=["copies"])


@router.post("/{product_id}/generate-copy")
def generate_copy(product_id: int, payload: CopyGenerateRequest | None = None, context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product or product.workspace_id != context.workspace_id:
        raise HTTPException(404, "商品不存在")
    try:
        return generate_copy_for_product(db, product_id, operator_name=context.operator_name, use_hot_search=payload.use_hot_search if payload else None)
    except ValueError as exc:
        raise HTTPException(400, detail=exc.args[0]) from exc
    except RuntimeError as exc:
        raise HTTPException(502, detail=str(exc)) from exc


@router.post("/{product_id}/generate-copy-job", response_model=CopyBatchRead)
def generate_copy_job(product_id: int, payload: CopyGenerateRequest | None = None, context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    try:
        return create_single_product_batch(
            db,
            context.workspace_id,
            product_id,
            context.operator_name,
            use_hot_search=payload.use_hot_search if payload else None,
        )
    except ValueError as exc:
        raise HTTPException(404, detail=str(exc)) from exc


@router.post("/{product_id}/rewrite-copy")
def rewrite_copy(product_id: int, payload: RewriteCopyRequest, context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product or product.workspace_id != context.workspace_id:
        raise HTTPException(404, "商品不存在")
    try:
        return rewrite_copy_for_product(db, product_id, payload.rewrite_instruction, payload.operator_name)
    except ValueError as exc:
        raise HTTPException(400, detail=exc.args[0]) from exc
    except RuntimeError as exc:
        raise HTTPException(502, detail=str(exc)) from exc


@router.put("/{product_id}/copy", response_model=CopyRead)
def save_copy(product_id: int, payload: CopySaveRequest, context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product or product.workspace_id != context.workspace_id:
        raise HTTPException(404, "商品不存在")
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
def validate_copy(product_id: int, payload: ValidateCopyRequest, context: AuthContext = Depends(get_workspace_context), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product or product.workspace_id != context.workspace_id:
        raise HTTPException(404, "商品不存在")
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
def versions(product_id: int, context: AuthContext = Depends(get_workspace_context), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product or product.workspace_id != context.workspace_id:
        raise HTTPException(404, "商品不存在")
    return (
        db.query(CopyVersion)
        .filter(CopyVersion.product_id == product_id)
        .order_by(CopyVersion.version_no.desc())
        .all()
    )


@router.post("/{product_id}/copy-versions/{version_id}/restore", response_model=CopyRead)
def restore_version(product_id: int, version_id: int, context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    version = db.get(CopyVersion, version_id)
    product = db.get(Product, product_id)
    if not product or product.workspace_id != context.workspace_id or not version or version.product_id != product_id:
        raise HTTPException(404, "版本不存在")
    output = db.query(CopyOutput).filter(CopyOutput.product_id == product_id).first()
    if not output:
        output = CopyOutput(product_id=product_id, workspace_id=context.workspace_id, created_by=context.operator_name)
        db.add(output)
        db.flush()
    output.title = version.title
    output.main_image_tags = version.main_image_tags
    output.color_copy = version.color_copy
    output.source_basis = "从历史版本恢复"
    output.status = "edited"
    output.updated_by = context.operator_name
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
