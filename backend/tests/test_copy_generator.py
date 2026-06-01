from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import CopyOutput, CopyVersion, Product, Rule
from app.services.copy_generator import generate_copy_for_product


def _add_product(db, **overrides):
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
        **overrides,
    )
    db.add(product)
    db.commit()
    return product


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
    product = _add_product(db)

    payload = generate_copy_for_product(db, product.id, operator_name="tester")

    assert payload["title"]
    assert len(payload["title"]) in (29, 30)
    assert payload["main_image_tags"] == ["清凉防晒", "透气不闷", "出游好穿"]
    assert payload["color_copy"] == "清爽显白"
    assert db.query(CopyOutput).count() == 1
    version = db.query(CopyVersion).one()
    assert version.version_type == "model_generated"
    assert version.version_no == 1


def test_generation_accepts_chinese_llm_field_names(monkeypatch):
    class ChineseKeyClient:
        provider = "openai_compatible"
        model = "fake"

        def generate_json(self, messages, schema_hint=None):
            return {
                "标题": "清凉防晒中大童女童防晒衣夏季出游轻薄舒适百搭好穿活力日常自在",
                "主图卖点": ["清凉防晒", "透气不闷", "出游好穿"],
                "颜色词文案": "清爽显白",
                "生成依据": "根据FBA、品类、季节和场景生成",
            }

    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setattr("app.services.copy_generator.get_llm_client", lambda db=None: ChineseKeyClient())
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    product = _add_product(db)

    payload = generate_copy_for_product(db, product.id, operator_name="tester")

    assert payload["title"] == "清凉防晒中大童女童防晒衣夏季出游轻薄舒适百搭好穿活力日常自在"
    assert payload["main_image_tags"] == ["清凉防晒", "透气不闷", "出游好穿"]
    assert payload["color_copy"] == "清爽显白"
    assert db.query(CopyOutput).count() == 1


def test_generation_repairs_invalid_llm_output_without_extra_model_call(monkeypatch):
    class InvalidClient:
        provider = "openai_compatible"
        model = "fake"

        def __init__(self):
            self.calls = 0

        def generate_json(self, messages, schema_hint=None):
            self.calls += 1
            return {"title": "防晒衣", "main_image_tags": [], "color_copy": ""}

    client = InvalidClient()
    monkeypatch.setenv("LLM_PROVIDER", "openai_compatible")
    monkeypatch.setenv("LLM_MAX_RETRIES", "2")
    monkeypatch.setattr("app.services.copy_generator.get_llm_client", lambda db=None: client)
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    db = Session()
    product = _add_product(db)

    payload = generate_copy_for_product(db, product.id, operator_name="tester")

    assert client.calls == 1
    assert len(payload["title"]) in (29, 30)
    assert payload["main_image_tags"] == ["清凉防晒", "透气不闷", "出游好穿"]
    assert payload["color_copy"] == "清爽显白"
