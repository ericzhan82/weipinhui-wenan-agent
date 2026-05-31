from openpyxl import load_workbook
from sqlalchemy.orm import Session

from app.models import Product, ProductSku

ALIASES = {
    "style_no": ["款号", "款式", "商品款号"],
    "product_no": ["货号", "商品货号"],
    "fba": ["FBA", "设计师卖点", "产品卖点"],
    "category_3": ["三级品类", "三类目"],
    "category_4": ["四级品类", "四类目"],
    "age_range": ["适用岁段", "适应岁段", "年龄段"],
    "gender": ["性别"],
    "season": ["季节"],
    "scene": ["场景"],
    "color_name": ["颜色", "颜色名称", "色系"],
    "color_code": ["色号"],
    "sku_no": ["SKC", "SKC/货号", "sku", "SKU"],
}


def _header_map(headers: list[str]) -> dict[str, int]:
    mapping: dict[str, int] = {}
    normalized = {str(header or "").strip(): index for index, header in enumerate(headers)}
    for field, names in ALIASES.items():
        for name in names:
            if name in normalized:
                mapping[field] = normalized[name]
                break
    return mapping


def _value(row: tuple, mapping: dict[str, int], field: str) -> str | None:
    index = mapping.get(field)
    if index is None or index >= len(row):
        return None
    value = row[index]
    return str(value).strip() if value is not None else None


def import_excel(db: Session, file_path: str) -> dict:
    workbook = load_workbook(file_path)
    sheet = workbook.active
    rows = list(sheet.iter_rows(values_only=True))
    if not rows:
        return {"success_count": 0, "failed_rows": [{"row": 1, "reason": "空文件"}], "skipped_count": 0}
    mapping = _header_map([str(cell or "").strip() for cell in rows[0]])
    success = 0
    skipped = 0
    failed: list[dict] = []
    for row_no, row in enumerate(rows[1:], start=2):
        style_no = _value(row, mapping, "style_no")
        product_no = _value(row, mapping, "product_no")
        if not style_no and not product_no:
            failed.append({"row": row_no, "reason": "缺少款号或货号"})
            continue
        existing = (
            db.query(Product)
            .filter(Product.style_no == style_no, Product.product_no == product_no)
            .first()
        )
        if existing:
            skipped += 1
            product = existing
        else:
            product = Product(
                style_no=style_no,
                product_no=product_no,
                category_3=_value(row, mapping, "category_3"),
                category_4=_value(row, mapping, "category_4"),
                age_range=_value(row, mapping, "age_range"),
                gender=_value(row, mapping, "gender"),
                season=_value(row, mapping, "season"),
                scene=_value(row, mapping, "scene"),
                fba=_value(row, mapping, "fba"),
                created_by="excel",
                updated_by="excel",
            )
            db.add(product)
            db.flush()
            success += 1
        sku_no = _value(row, mapping, "sku_no")
        color_name = _value(row, mapping, "color_name")
        if sku_no or color_name:
            db.add(
                ProductSku(
                    product_id=product.id,
                    sku_no=sku_no,
                    color_name=color_name,
                    color_code=_value(row, mapping, "color_code"),
                )
            )
    db.commit()
    return {"success_count": success, "failed_rows": failed, "skipped_count": skipped}
