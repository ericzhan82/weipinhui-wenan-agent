from openpyxl import Workbook
from sqlalchemy import create_engine
from sqlalchemy.orm import sessionmaker

from app.db import Base
from app.models import Product
from app.services.excel_importer import import_excel


def _session():
    engine = create_engine("sqlite:///:memory:")
    Base.metadata.create_all(engine)
    Session = sessionmaker(bind=engine)
    return Session()


def test_import_excel_detects_header_below_group_row(tmp_path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["", "", "", "", "", "需智能体辅助输出"])
    sheet.append(["款号", "货号", "三级分类名称", "尺码段", "性别", "季节", "场景", "FBA设计师卖点"])
    sheet.append(["209226141024", "20922614102460301", "儿童凉鞋", "21-33", "女童", "夏季", "户外出游", "魔术贴穿脱方便"])
    sheet.append(["", "", "", "", "", "", "", ""])
    path = tmp_path / "history.xlsx"
    workbook.save(path)

    db = _session()
    result = import_excel(db, str(path))

    product = db.query(Product).one()
    assert result["success_count"] == 1
    assert result["failed_rows"] == []
    assert product.style_no == "209226141024"
    assert product.product_no == "20922614102460301"
    assert product.category_3 == "儿童凉鞋"
    assert product.age_range == "21-33"
    assert product.fba == "魔术贴穿脱方便"


def test_import_excel_updates_existing_blank_context_and_deduplicates_skus(tmp_path):
    workbook = Workbook()
    sheet = workbook.active
    sheet.append(["款号", "货号", "三级品类", "四级品类", "FBA", "颜色", "SKC"])
    sheet.append(["A100", "P100", "儿童凉鞋", "包头凉鞋", "轻便防滑", "米白", "SKU100"])
    path = tmp_path / "products.xlsx"
    workbook.save(path)

    db = _session()
    db.add(Product(style_no="A100", product_no="P100", workspace_id=1))
    db.commit()

    first = import_excel(db, str(path), workspace_id=1)
    second = import_excel(db, str(path), workspace_id=1)

    product = db.query(Product).one()
    assert first["updated_count"] == 1
    assert second["updated_count"] == 0
    assert product.category_3 == "儿童凉鞋"
    assert product.category_4 == "包头凉鞋"
    assert product.fba == "轻便防滑"
    assert product.status == "ready"
    assert len(product.skus) == 1
