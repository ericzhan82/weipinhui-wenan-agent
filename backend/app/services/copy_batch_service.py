from __future__ import annotations

import os
import time
import logging
import threading
from datetime import datetime
from uuid import uuid4

from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db import SessionLocal
from app.models import CopyBatch, CopyBatchItem, Product, now
from app.services.copy_generator import generate_copy_for_product

logger = logging.getLogger(__name__)
_WORKER_LOCK = threading.Lock()
_WORKERS_STARTED = False
PRODUCT_READY_STATUSES = {"draft", "ready", "queued", "generating", "generated", "failed"}


def make_batch_no() -> str:
    return f"COPY-{datetime.now().strftime('%Y%m%d-%H%M%S')}-{uuid4().hex[:4].upper()}"


def product_context_ready(product: Product) -> bool:
    return bool(
        (product.category_3 or "").strip()
        and (product.category_4 or "").strip()
        and (product.fba or "").strip()
    )


def product_has_copy(product: Product) -> bool:
    return bool(product.copy_output and (product.copy_output.title or "").strip())


def sync_product_status(product: Product) -> None:
    if product_has_copy(product):
        product.status = "generated"
    elif product_context_ready(product):
        product.status = "ready"
    elif product.status not in {"queued", "generating", "failed"}:
        product.status = "draft"


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
    products = query.order_by(Product.updated_at.desc()).all()
    context_status = filters.get("context_status")
    if context_status == "ready":
        products = [product for product in products if product_context_ready(product)]
    elif context_status == "missing":
        products = [product for product in products if not product_context_ready(product)]
    copy_state = filters.get("copy_state")
    if copy_state == "generated":
        products = [product for product in products if product_has_copy(product)]
    elif copy_state == "not_generated":
        products = [product for product in products if not product_has_copy(product)]
    return products


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
    agent_mode: str | None = None,
) -> CopyBatch:
    products = _product_query(db, workspace_id, filters)
    batch = CopyBatch(
        workspace_id=workspace_id,
        batch_no=make_batch_no(),
        status="queued",
        filter_json=filters,
        overwrite_existing=overwrite_existing,
        use_hot_search=use_hot_search,
        agent_mode=agent_mode,
        created_by=created_by,
    )
    db.add(batch)
    db.flush()
    for product in products:
        status = "pending"
        if product.copy_output and product.copy_output.title and not overwrite_existing:
            status = "skipped"
        elif product.status in PRODUCT_READY_STATUSES:
            product.status = "queued"
            product.updated_by = created_by
        db.add(CopyBatchItem(batch_id=batch.id, product_id=product.id, status=status))
    db.flush()
    _recount_batch(db, batch)
    db.commit()
    db.refresh(batch)
    return batch


def create_single_product_batch(
    db: Session,
    workspace_id: int,
    product_id: int,
    created_by: str,
    use_hot_search: bool | None = None,
    agent_mode: str | None = None,
) -> CopyBatch:
    product = db.get(Product, product_id)
    if not product or product.workspace_id != workspace_id:
        raise ValueError("商品不存在")
    batch = CopyBatch(
        workspace_id=workspace_id,
        batch_no=make_batch_no(),
        status="queued",
        filter_json={"product_id": product_id, "mode": "single"},
        overwrite_existing=True,
        use_hot_search=use_hot_search,
        agent_mode=agent_mode,
        created_by=created_by,
    )
    product.status = "queued"
    product.updated_by = created_by
    db.add(batch)
    db.flush()
    db.add(CopyBatchItem(batch_id=batch.id, product_id=product.id, status="pending"))
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
        product = db.get(Product, item.product_id)
        if product:
            sync_product_status(product)
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
        product = db.get(Product, item.product_id)
        if product:
            product.status = "queued"
            product.updated_by = batch.created_by
    batch.finished_at = None
    _recount_batch(db, batch)
    db.commit()
    db.refresh(batch)
    return batch


def recover_running_batches(db: Session) -> None:
    for batch in db.query(CopyBatch).filter(CopyBatch.status == "canceling").all():
        for item in db.query(CopyBatchItem).filter(
            CopyBatchItem.batch_id == batch.id,
            CopyBatchItem.status.in_(["pending", "running"]),
        ).all():
            item.status = "canceled"
            item.finished_at = now()
            product = db.get(Product, item.product_id)
            if product:
                sync_product_status(product)
        _recount_batch(db, batch)
        batch.status = "canceled"
        batch.finished_at = batch.finished_at or now()
    running_batch_ids = [batch.id for batch in db.query(CopyBatch).filter(CopyBatch.status == "running").all()]
    if running_batch_ids:
        for item in db.query(CopyBatchItem).filter(CopyBatchItem.batch_id.in_(running_batch_ids), CopyBatchItem.status == "running").all():
            item.status = "pending"
            item.started_at = None
    for batch in db.query(CopyBatch).filter(CopyBatch.status == "running").all():
        batch.status = "queued"
        batch.started_at = None
        _recount_batch(db, batch)
    db.commit()


def _next_work_item(db: Session) -> tuple[CopyBatch, CopyBatchItem] | None:
    item = (
        db.query(CopyBatchItem)
        .join(CopyBatch, CopyBatch.id == CopyBatchItem.batch_id)
        .filter(CopyBatch.status.in_(["queued", "running"]))
        .filter(CopyBatchItem.status == "pending")
        .order_by(CopyBatch.created_at.asc(), CopyBatch.id.asc(), CopyBatchItem.id.asc())
        .with_for_update(skip_locked=True)
        .first()
    )
    if not item:
        for batch in db.query(CopyBatch).filter(CopyBatch.status.in_(["queued", "running"])).all():
            _recount_batch(db, batch)
        db.commit()
        return None
    batch = db.get(CopyBatch, item.batch_id)
    if not batch:
        db.rollback()
        return None
    if batch.status == "canceling":
        item.status = "canceled"
        item.finished_at = now()
        _recount_batch(db, batch)
        db.commit()
        return None
    batch.status = "running"
    batch.started_at = batch.started_at or now()
    item.status = "running"
    item.started_at = now()
    product = db.get(Product, item.product_id)
    if product:
        product.status = "generating"
        product.updated_by = batch.created_by
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
                agent_mode=batch.agent_mode,
            )
            item.status = "success"
            item.error_message = None
        except Exception as exc:  # noqa: BLE001 - batch item must record and continue
            item.status = "failed"
            item.error_message = str(exc)[:1000]
            product = db.get(Product, item.product_id)
            if product:
                product.status = "failed"
                product.updated_by = batch.created_by
        item.finished_at = now()
        _recount_batch(db, batch)
        db.commit()
        return True
    finally:
        db.close()


def _worker_loop() -> None:
    interval = float(os.getenv("COPY_BATCH_WORKER_POLL_SECONDS", "2"))
    while True:
        try:
            did_work = _process_one()
        except Exception:  # noqa: BLE001 - worker must survive transient database/model failures
            logger.exception("copy batch worker loop failed; retrying after poll interval")
            time.sleep(interval)
            continue
        if not did_work:
            time.sleep(interval)


def start_copy_batch_workers() -> None:
    global _WORKERS_STARTED
    if _WORKERS_STARTED:
        return
    _WORKERS_STARTED = True
    workers = max(1, min(4, int(os.getenv("COPY_BATCH_WORKER_CONCURRENCY", "1"))))
    for index in range(workers):
        thread = threading.Thread(target=_worker_loop, name=f"copy-batch-worker-{index + 1}", daemon=True)
        thread.start()


def run_copy_batch_workers_forever() -> None:
    workers = max(1, min(4, int(os.getenv("COPY_BATCH_WORKER_CONCURRENCY", "1"))))
    for index in range(max(0, workers - 1)):
        thread = threading.Thread(target=_worker_loop, name=f"copy-batch-worker-{index + 2}", daemon=True)
        thread.start()
    logger.info("copy batch worker started with concurrency=%s", workers)
    _worker_loop()
