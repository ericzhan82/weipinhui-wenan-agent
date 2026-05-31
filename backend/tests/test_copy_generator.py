from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import CopyOutput, CopyVersion, Product, Rule
from app.services.copy_generator import generate_copy_for_product


def test_mock_generation_creates_output_and_model_version(monkeypatch):
    monkeypatch.setenv("LLM_PROVIDER", "mock")
    monkeypatch.setenv("LLM_MODEL", "mock")
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    db.add(
        Rule(
            rule_type="forbidden",
            rule_name="禁用词",
            content="最强\n第一",
            enabled=True,
        )
    )
    product = Product(
        style_no="A100",
        product_no="P100",
        category_3="外套",
        category_4="防晒衣",
        age_range="中大童",
        gender="女童",
        season="夏季",
        scene="出游",
        fba="清凉防晒，透气不闷，轻薄好穿",
        created_by="tester",
        updated_by="tester",
    )
    db.add(product)
    db.commit()

    payload = generate_copy_for_product(db, product.id, operator_name="tester")

    assert payload["title"]
    assert len(payload["title"]) in (29, 30)
    assert payload["main_image_tags"] == ["清凉防晒", "透气不闷", "出游好穿"]
    assert payload["color_copy"] == "清爽显白"
    assert db.query(CopyOutput).count() == 1
    version = db.query(CopyVersion).one()
    assert version.version_type == "model_generated"
    assert version.version_no == 1
