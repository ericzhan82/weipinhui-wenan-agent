from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import CopyBatch, CopyBatchItem, CopyOutput, Product, Workspace
from app.services import copy_batch_service
from app.services.copy_batch_service import create_copy_batch, create_single_product_batch, recover_running_batches


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_create_copy_batch_snapshots_filter_and_skips_existing_outputs():
    db = _session()
    workspace = Workspace(name="Default", slug="default")
    db.add(workspace)
    db.flush()
    first = Product(workspace_id=workspace.id, style_no="A100", product_no="P100", category_3="Kids", category_4="Shoes", fba="easy wear")
    second = Product(workspace_id=workspace.id, style_no="A200", product_no="P200", category_3="Kids", category_4="Shoes", fba="soft")
    other_workspace = Product(workspace_id=999, style_no="A300", product_no="P300", category_3="Kids", category_4="Shoes", fba="other")
    db.add_all([first, second, other_workspace])
    db.flush()
    db.add(CopyOutput(workspace_id=workspace.id, product_id=second.id, title="already generated", main_image_tags=[], color_copy="done"))
    db.commit()

    batch = create_copy_batch(
        db,
        workspace.id,
        "tester",
        {"keyword": "A"},
        overwrite_existing=False,
        use_hot_search=True,
    )

    statuses = sorted(
        item.status
        for item in db.query(CopyBatchItem)
        .filter(CopyBatchItem.batch_id == batch.id)
        .all()
    )

    assert batch.total_count == 2
    assert batch.pending_count == 1
    assert batch.skipped_count == 1
    assert batch.use_hot_search is True
    assert statuses == ["pending", "skipped"]
    db.refresh(first)
    assert first.status == "queued"


def test_create_copy_batch_filters_context_and_copy_state():
    db = _session()
    workspace = Workspace(name="Default", slug="default")
    db.add(workspace)
    db.flush()
    ready = Product(workspace_id=workspace.id, style_no="A100", product_no="P100", category_3="Kids", category_4="Shoes", fba="easy wear")
    missing = Product(workspace_id=workspace.id, style_no="A200", product_no="P200", category_3="Kids")
    generated = Product(workspace_id=workspace.id, style_no="A300", product_no="P300", category_3="Kids", category_4="Tee", fba="soft")
    db.add_all([ready, missing, generated])
    db.flush()
    db.add(CopyOutput(workspace_id=workspace.id, product_id=generated.id, title="already generated", main_image_tags=[], color_copy="done"))
    db.commit()

    batch = create_copy_batch(
        db,
        workspace.id,
        "tester",
        {"context_status": "ready", "copy_state": "not_generated"},
        overwrite_existing=False,
    )

    items = db.query(CopyBatchItem).filter(CopyBatchItem.batch_id == batch.id).all()
    assert [item.product_id for item in items] == [ready.id]


def test_create_single_product_batch_queues_exact_product():
    db = _session()
    workspace = Workspace(name="Default", slug="default")
    db.add(workspace)
    db.flush()
    product = Product(workspace_id=workspace.id, style_no="A100", product_no="P100", category_3="Kids", category_4="Shoes", fba="easy wear")
    other = Product(workspace_id=workspace.id, style_no="A200", product_no="P200", category_3="Kids", category_4="Shoes", fba="soft")
    db.add_all([product, other])
    db.commit()

    batch = create_single_product_batch(db, workspace.id, product.id, "tester", use_hot_search=False)

    items = db.query(CopyBatchItem).filter(CopyBatchItem.batch_id == batch.id).all()
    db.refresh(product)
    db.refresh(other)
    assert batch.total_count == 1
    assert items[0].product_id == product.id
    assert items[0].status == "pending"
    assert product.status == "queued"
    assert other.status == "draft"


def test_recover_running_batches_preserves_canceling_intent():
    db = _session()
    workspace = Workspace(name="Default", slug="default")
    db.add(workspace)
    db.flush()
    product = Product(workspace_id=workspace.id, style_no="A100", product_no="P100")
    db.add(product)
    db.flush()
    batch = CopyBatch(workspace_id=workspace.id, batch_no="COPY-1", status="canceling", total_count=1, running_count=1)
    db.add(batch)
    db.flush()
    db.add(CopyBatchItem(batch_id=batch.id, product_id=product.id, status="running"))
    db.commit()

    recover_running_batches(db)

    db.refresh(batch)
    item = db.query(CopyBatchItem).one()
    assert batch.status == "canceled"
    assert batch.canceled_count == 1
    assert item.status == "canceled"


def test_worker_process_one_handles_empty_queue(monkeypatch):
    db = _session()
    workspace = Workspace(name="Default", slug="default")
    db.add(workspace)
    db.commit()
    monkeypatch.setattr(copy_batch_service, "SessionLocal", lambda: db)

    assert copy_batch_service._process_one() is False
