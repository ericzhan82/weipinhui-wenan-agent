from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import CopyBatchItem, CopyOutput, Product, Workspace
from app.services.copy_batch_service import create_copy_batch


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
