from pathlib import Path

from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import HotSearchBatch, HotSearchTerm, Product, Rule
from app.services.hot_search_service import (
    evaluate_hot_title,
    get_hot_search_config,
    import_hot_search_file,
    select_hot_terms_for_product,
    set_hot_search_config,
)


def _db():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def _write_hot_search_workbook(path: Path, rows: list[list[object]]) -> None:
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(
        [
            "排名",
            "搜索词主分类",
            "关键词",
            "搜索UV指数",
            "机会指数",
            "成交金额指数",
            "销售量指数",
        ]
    )
    for row in rows:
        sheet.append(row)
    workbook.save(path)


def test_import_hot_search_file_saves_terms_by_batch(tmp_path):
    db = _db()
    file_path = tmp_path / "hot-search.xlsx"
    _write_hot_search_workbook(
        file_path,
        [
            [1, "儿童裤子", "男童裤子薄款", 1000, 4, 30000, 500],
            [2, "儿童裤子", "儿童裤子", 900, 3, 28000, 450],
        ],
    )

    result = import_hot_search_file(db, str(file_path), uploaded_by="tester")

    assert result["imported_count"] == 2
    assert result["categories"] == ["儿童裤子"]
    assert db.query(HotSearchBatch).count() == 1
    terms = db.query(HotSearchTerm).order_by(HotSearchTerm.rank.asc()).all()
    assert [term.keyword for term in terms] == ["男童裤子薄款", "儿童裤子"]
    assert terms[0].search_uv_index == 1000


def test_hot_search_config_defaults_off_and_can_be_enabled():
    db = _db()

    assert get_hot_search_config(db)["enabled_by_default"] is False

    config = set_hot_search_config(db, enabled_by_default=True, updated_by="tester")

    assert config["enabled_by_default"] is True
    assert get_hot_search_config(db)["enabled_by_default"] is True


def test_select_hot_terms_filters_avoid_terms_and_gender():
    db = _db()
    db.add(Rule(rule_type="hot_search_avoid_terms", rule_name="中童", content="巴拉巴拉,旗舰店", enabled=True))
    batch = HotSearchBatch(filename="source.xlsx", uploaded_by="tester")
    db.add(batch)
    db.flush()
    db.add_all(
        [
            HotSearchTerm(batch_id=batch.id, category="儿童裤子", keyword="男童裤子薄款", rank=1),
            HotSearchTerm(batch_id=batch.id, category="儿童裤子", keyword="女童裤子薄款", rank=2),
            HotSearchTerm(batch_id=batch.id, category="儿童裤子", keyword="巴拉巴拉儿童裤子", rank=3),
            HotSearchTerm(batch_id=batch.id, category="儿童裤子", keyword="儿童裤子", rank=4),
        ]
    )
    product = Product(category_3="儿童裤子", age_range="中童", gender="男")
    db.add(product)
    db.commit()

    result = select_hot_terms_for_product(db, product)

    assert result["selected_hot_terms"] == ["男童裤子薄款", "儿童裤子"]
    assert {"keyword": "女童裤子薄款", "reason": "gender_conflict"} in result["excluded_hot_terms"]
    assert {"keyword": "巴拉巴拉儿童裤子", "reason": "avoid_term:巴拉巴拉"} in result["excluded_hot_terms"]
    assert result["hot_search_source_batch"] == batch.id


def test_evaluate_hot_title_requires_complete_term_match():
    result = evaluate_hot_title(
        "清凉舒适男童裤子薄款夏季儿童长裤轻便透气百搭好穿",
        ["男童裤子薄款", "儿童裤子", "女童裤子"],
    )

    assert result["matched_hot_terms"] == ["男童裤子薄款"]
    assert result["missing_hot_terms"] == ["儿童裤子", "女童裤子"]
