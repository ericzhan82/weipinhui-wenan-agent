from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import CopyOutput, HotSearchBatch, HotSearchTerm, Product, Rule
from app.services.copy_generator import generate_copy_for_product
from app.services.hot_search_service import set_hot_search_config
import pytest


def _add_product(db, **overrides):
    payload = {
        "style_no": "A100",
        "product_no": "P100",
        "category_3": "儿童裤子",
        "category_4": "长裤",
        "age_range": "中童",
        "gender": "男",
        "season": "夏季",
        "scene": "日常",
        "fba": "清凉透气，轻薄好穿，舒适百搭",
        "created_by": "tester",
        "updated_by": "tester",
    }
    payload.update(overrides)
    product = Product(**payload)
    db.add(product)
    db.commit()
    return product


def _db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def _add_hot_terms(db):
    batch = HotSearchBatch(filename="source.xlsx", uploaded_by="tester")
    db.add(batch)
    db.flush()
    db.add_all(
        [
            HotSearchTerm(batch_id=batch.id, category="儿童裤子", keyword="男童裤子薄款", rank=1),
            HotSearchTerm(batch_id=batch.id, category="儿童裤子", keyword="女童裤子薄款", rank=2),
            HotSearchTerm(batch_id=batch.id, category="儿童裤子", keyword="巴拉巴拉儿童裤子", rank=3),
        ]
    )
    db.commit()
    return batch


class RecordingClient:
    provider = "openai_compatible"
    model = "fake"

    def __init__(self):
        self.messages = []

    def generate_json(self, messages, schema_hint=None):
        self.messages = messages
        return {
            "title": "清凉透气轻薄男童裤子薄款夏季儿童长裤舒适百搭好穿日常自在出游",
            "main_image_tags": ["清凉透气", "轻薄好穿", "日常百搭"],
            "color_copy": "清爽蓝白",
            "source_basis": "根据商品资料和热搜词生成",
            "warnings": [],
        }


def test_generation_keeps_hot_search_disabled_by_default(monkeypatch):
    client = RecordingClient()
    monkeypatch.setattr("app.services.copy_generator.get_llm_client", lambda db=None: client)
    db = _db()
    product = _add_product(db)
    _add_hot_terms(db)

    payload = generate_copy_for_product(db, product.id, operator_name="tester")

    assert payload["hot_search_enabled"] is False
    assert payload["selected_hot_terms"] == []
    assert "男童裤子薄款" not in str(client.messages)


def test_generation_uses_hot_search_when_requested(monkeypatch):
    client = RecordingClient()
    monkeypatch.setattr("app.services.copy_generator.get_llm_client", lambda db=None: client)
    db = _db()
    product = _add_product(db)
    db.add(Rule(rule_type="hot_search_avoid_terms", rule_name="中童", content="巴拉巴拉", enabled=True))
    _add_hot_terms(db)

    payload = generate_copy_for_product(db, product.id, operator_name="tester", use_hot_search=True)

    assert payload["hot_search_enabled"] is True
    assert payload["selected_hot_terms"] == ["男童裤子薄款"]
    assert payload["matched_hot_terms"] == ["男童裤子薄款"]
    assert payload["missing_hot_terms"] == []
    assert {"keyword": "女童裤子薄款", "reason": "gender_conflict"} in payload["excluded_hot_terms"]
    assert "男童裤子薄款" in str(client.messages)


def test_generation_global_hot_search_can_be_overridden_off(monkeypatch):
    client = RecordingClient()
    monkeypatch.setattr("app.services.copy_generator.get_llm_client", lambda db=None: client)
    db = _db()
    set_hot_search_config(db, enabled_by_default=True, updated_by="tester")
    product = _add_product(db)
    _add_hot_terms(db)

    payload = generate_copy_for_product(db, product.id, operator_name="tester", use_hot_search=False)

    assert payload["hot_search_enabled"] is False
    assert payload["selected_hot_terms"] == []
    assert "男童裤子薄款" not in str(client.messages)


def test_generation_with_hot_search_fails_without_matching_terms_before_model_call(monkeypatch):
    client = RecordingClient()
    monkeypatch.setattr("app.services.copy_generator.get_llm_client", lambda db=None: client)
    db = _db()
    product = _add_product(db, category_3="儿童泳装泳具")

    with pytest.raises(ValueError) as exc:
        generate_copy_for_product(db, product.id, operator_name="tester", use_hot_search=True)

    assert exc.value.args[0]["message"] == "未找到可用热搜词"
    assert client.messages == []
    assert db.query(CopyOutput).count() == 0


def test_generation_with_hot_search_does_not_overwrite_existing_title_when_model_misses_term(monkeypatch):
    class MissingTermClient(RecordingClient):
        def generate_json(self, messages, schema_hint=None):
            self.messages = messages
            return {
                "title": "清凉透气中童男童长裤夏季日常轻薄舒适百搭好穿自在活力清爽好",
                "main_image_tags": ["清凉透气", "轻薄好穿", "日常百搭"],
                "color_copy": "清爽蓝白",
                "source_basis": "故意缺少完整热搜词",
                "warnings": [],
            }

    client = MissingTermClient()
    monkeypatch.setattr("app.services.copy_generator.get_llm_client", lambda db=None: client)
    db = _db()
    product = _add_product(db)
    db.add(
        CopyOutput(
            product_id=product.id,
            title="原有标题保持不变男童长裤夏季轻薄舒适百搭好穿自在清爽",
            main_image_tags=["原有卖点"],
            color_copy="原有颜色",
        )
    )
    db.add(Rule(rule_type="hot_search_avoid_terms", rule_name="中童", content="", enabled=True))
    _add_hot_terms(db)

    with pytest.raises(ValueError) as exc:
        generate_copy_for_product(db, product.id, operator_name="tester", use_hot_search=True)

    db.expire_all()
    current = db.query(CopyOutput).filter(CopyOutput.product_id == product.id).one()
    assert "标题未完整包含热搜词：男童裤子薄款" in str(exc.value.args[0])
    assert current.title == "原有标题保持不变男童长裤夏季轻薄舒适百搭好穿自在清爽"
    assert current.color_copy == "原有颜色"
