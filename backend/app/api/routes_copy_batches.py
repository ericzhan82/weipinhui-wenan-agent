from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_workspace_context, require_workspace_write
from app.db import get_db
from app.schemas import CopyBatchCreate, CopyBatchDetail, CopyBatchRead
from app.services.copy_batch_service import (
    cancel_copy_batch,
    create_copy_batch,
    get_copy_batch,
    list_copy_batches,
    retry_failed_items,
)
from app.services.excel_exporter import export_copy_batch
from app.api.routes_excel import storage_dir

router = APIRouter(prefix="/api/copy-batches", tags=["copy-batches"])


@router.post("", response_model=CopyBatchRead)
def create_batch(
    payload: CopyBatchCreate,
    context: AuthContext = Depends(require_workspace_write),
    db: Session = Depends(get_db),
):
    filters = payload.model_dump(include={"keyword", "status", "gender", "season", "context_status", "copy_state"}, exclude_none=True)
    return create_copy_batch(
        db,
        context.workspace_id,
        context.operator_name,
        filters,
        overwrite_existing=payload.overwrite_existing,
        use_hot_search=payload.use_hot_search,
    )


@router.get("", response_model=list[CopyBatchRead])
def batches(context: AuthContext = Depends(get_workspace_context), db: Session = Depends(get_db)):
    return list_copy_batches(db, context.workspace_id)


@router.get("/{batch_no}", response_model=CopyBatchDetail)
def batch_detail(batch_no: str, context: AuthContext = Depends(get_workspace_context), db: Session = Depends(get_db)):
    batch = get_copy_batch(db, context.workspace_id, batch_no)
    if not batch:
        raise HTTPException(404, "批量任务不存在")
    return {"batch": batch, "items": batch_items(db, batch.id)}


def batch_items(db: Session, batch_id: int):
    from app.models import CopyBatchItem

    return db.query(CopyBatchItem).filter(CopyBatchItem.batch_id == batch_id).order_by(CopyBatchItem.id).all()


@router.post("/{batch_no}/cancel", response_model=CopyBatchRead)
def cancel_batch(batch_no: str, context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    batch = get_copy_batch(db, context.workspace_id, batch_no)
    if not batch:
        raise HTTPException(404, "批量任务不存在")
    if batch.created_by != context.operator_name and context.role not in {"system_admin", "workspace_admin"} and not context.user.is_system_admin:
        raise HTTPException(403, "只有创建者或管理员可以取消任务")
    return cancel_copy_batch(db, batch)


@router.post("/{batch_no}/retry-failed", response_model=CopyBatchRead)
def retry_failed(batch_no: str, context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    batch = get_copy_batch(db, context.workspace_id, batch_no)
    if not batch:
        raise HTTPException(404, "批量任务不存在")
    if batch.created_by != context.operator_name and context.role not in {"system_admin", "workspace_admin"} and not context.user.is_system_admin:
        raise HTTPException(403, "只有创建者或管理员可以重试任务")
    return retry_failed_items(db, batch)


@router.get("/{batch_no}/export")
def export_batch(batch_no: str, context: AuthContext = Depends(get_workspace_context), db: Session = Depends(get_db)):
    batch = get_copy_batch(db, context.workspace_id, batch_no)
    if not batch:
        raise HTTPException(404, "批量任务不存在")
    result = export_copy_batch(db, str(storage_dir()), batch)
    return {
        "export_id": result["export_id"],
        "filename": result["filename"],
        "download_url": f"/api/excel/export/{result['export_id']}/download",
    }
