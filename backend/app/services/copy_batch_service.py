from __future__ import annotations

import os
import threading
import time
from datetime import datetime
from uuid import uuid4

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import CopyBatch, CopyBatchItem, Product, now
from app.services.copy_generator import generate_copy_for_product

_WORKERS_STARTED = False
_WORKER_LOCK = threading.Lock()


def make_batch_no() -> str:
    return f"COPY-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:4].upper()}"


def _product_query(db: Session, workspace_id: int, filters: dict) -> list[Product]:
    query = db.query(Product).filter(Product.workspace_id == workspace_id)
    keyword = filters.get("keyword")
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                Product.style_no.like(like),
                Product.product_no.like(like),
                Product.category_3.like(like),
                Product.category_4.like(like),
                Product.fba.like(like),
            )
        )
    if filters.get("status"):
        query = query.filter(Product.status == filters["status"])
    if filters.get("gender"):
        query = query.filter(Product.gender == filters["gender"])
    if filters.get("season"):
        query = query.filter(Product.season == filters["season"])
    return query.order_by(Product.updated_at.desc()).all()


def _recount_batch(db: Session, batch: CopyBatch) -> None:
    items = db.query(CopyBatchItem).filter(CopyBatchItem.batch_id == batch.id).all()
    counts = {status: 0 for status in ["pending", "running", "success", "failed", "skipped", "canceled"]}
    for item in items:
        counts[item.status] = counts.get(item.status, 0) + 1
    batch.total_count = len(items)
    batch.pending_count = counts["pending"]
    batch.running_count = counts["running"]
    batch.success_count = counts["success"]
    batch.failed_count = counts["failed"]
    batch.skipped_count = counts["skipped"]
    batch.canceled_count = counts["canceled"]
    if batch.status not in {"canceling", "canceled"}:
        if batch.pending_count or batch.running_count:
            batch.status = "running" if batch.started_at else "queued"
        elif batch.failed_count:
            batch.status = "completed_with_errors"
            batch.finished_at = batch.finished_at or now()
        else:
            batch.status = "completed"
            batch.finished_at = batch.finished_at or now()


def create_copy_batch(
    db: Session,
    workspace_id: int,
    created_by: str,
    filters: dict,
    overwrite_existing: bool = False,
    use_hot_search: bool | None = None,
) -> CopyBatch:
    products = _product_query(db, workspace_id, filters)
    batch = CopyBatch(
        workspace_id=workspace_id,
        batch_no=make_batch_no(),
        status="queued",
        filter_json=filters,
        overwrite_existing=overwrite_existing,
        use_hot_search=use_hot_search,
        created_by=created_by,
    )
    db.add(batch)
    db.flush()
    for product in products:
        status = "pending"
        if product.copy_output and product.copy_output.title and not overwrite_existing:
            status = "skipped"
        db.add(CopyBatchItem(batch_id=batch.id, product_id=product.id, status=status))
    db.flush()
    _recount_batch(db, batch)
    db.commit()
    db.refresh(batch)
    return batch


def list_copy_batches(db: Session, workspace_id: int) -> list[CopyBatch]:
    return db.query(CopyBatch).filter(CopyBatch.workspace_id == workspace_id).order_by(CopyBatch.created_at.desc()).all()


def get_copy_batch(db: Session, workspace_id: int, batch_no: str) -> CopyBatch | None:
    return db.query(CopyBatch).filter(CopyBatch.workspace_id == workspace_id, CopyBatch.batch_no == batch_no).first()


def cancel_copy_batch(db: Session, batch: CopyBatch) -> CopyBatch:
    batch.status = "canceling"
    for item in db.query(CopyBatchItem).filter(CopyBatchItem.batch_id == batch.id, CopyBatchItem.status == "pending").all():
        item.status = "canceled"
        item.finished_at = now()
    _recount_batch(db, batch)
    if batch.running_count == 0:
        batch.status = "canceled"
        batch.finished_at = batch.finished_at or now()
    db.commit()
    db.refresh(batch)
    return batch


def retry_failed_items(db: Session, batch: CopyBatch) -> CopyBatch:
    if batch.status in {"canceling", "canceled"}:
        batch.status = "queued"
    for item in db.query(CopyBatchItem).filter(CopyBatchItem.batch_id == batch.id, CopyBatchItem.status == "failed").all():
        item.status = "pending"
        item.error_message = None
        item.started_at = None
        item.finished_at = None
    batch.finished_at = None
    _recount_batch(db, batch)
    db.commit()
    db.refresh(batch)
    return batch


def recover_running_batches(db: Session) -> None:
    for item in db.query(CopyBatchItem).filter(CopyBatchItem.status == "running").all():
        item.status = "pending"
        item.started_at = None
    for batch in db.query(CopyBatch).filter(CopyBatch.status.in_(["running", "canceling"])).all():
        batch.status = "queued"
        batch.started_at = None
    db.commit()


def _next_work_item(db: Session) -> tuple[CopyBatch, CopyBatchItem] | None:
    batch = (
        db.query(CopyBatch)
        .filter(CopyBatch.status.in_(["queued", "running"]))
        .order_by(CopyBatch.created_at.asc(), CopyBatch.id.asc())
        .first()
    )
    if not batch:
        return None
    item = (
        db.query(CopyBatchItem)
        .filter(CopyBatchItem.batch_id == batch.id, CopyBatchItem.status == "pending")
        .order_by(CopyBatchItem.id.asc())
        .first()
    )
    if not item:
        _recount_batch(db, batch)
        db.commit()
        return None
    batch.status = "running"
    batch.started_at = batch.started_at or now()
    item.status = "running"
    item.started_at = now()
    db.commit()
    db.refresh(batch)
    db.refresh(item)
    return batch, item


def _process_one() -> bool:
    db = SessionLocal()
    try:
        with _WORKER_LOCK:
            work = _next_work_item(db)
        if not work:
            return False
        batch, item = work
        try:
            generate_copy_for_product(
                db,
                item.product_id,
                operator_name=batch.created_by or "batch",
                use_hot_search=batch.use_hot_search,
            )
            item.status = "success"
            item.error_message = None
        except Exception as exc:  # noqa: BLE001 - batch item must record and continue
            item.status = "failed"
            item.error_message = str(exc)[:1000]
        item.finished_at = now()
        _recount_batch(db, batch)
        db.commit()
        return True
    finally:
        db.close()


def _worker_loop() -> None:
    interval = float(os.getenv("COPY_BATCH_WORKER_POLL_SECONDS", "2"))
    while True:
        did_work = _process_one()
        if not did_work:
            time.sleep(interval)


def start_copy_batch_workers() -> None:
    global _WORKERS_STARTED
    if _WORKERS_STARTED:
        return
    _WORKERS_STARTED = True
    workers = max(1, min(2, int(os.getenv("COPY_BATCH_WORKER_CONCURRENCY", "1"))))
    for index in range(workers):
        thread = threading.Thread(target=_worker_loop, name=f"copy-batch-worker-{index + 1}", daemon=True)
        thread.start()
