from pathlib import Path
from uuid import uuid4

from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.models import Product

HEADERS = [
    "款号",
    "货号",
    "三级品类",
    "四级品类",
    "适用岁段",
    "性别",
    "季节",
    "场景",
    "FBA",
    "颜色",
    "色号",
    "SKC",
    "图片链接",
    "颜色备注",
    "备注",
    "唯品标题",
    "主图打标卖点",
    "颜色词文案",
]


def export_products(db: Session, storage_dir: str, keyword: str | None = None) -> dict:
    export_dir = Path(storage_dir) / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    query = db.query(Product)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(Product.style_no.like(like) | Product.product_no.like(like))
    products = query.order_by(Product.created_at.desc()).all()
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "唯品文案导出"
    sheet.append(HEADERS)
    for product in products:
        skus = product.skus or [None]
        for sku in skus:
            output = product.copy_output
            sheet.append(
                [
                    product.style_no,
                    product.product_no,
                    product.category_3,
                    product.category_4,
                    product.age_range,
                    product.gender,
                    product.season,
                    product.scene,
                    product.fba,
                    sku.color_name if sku else "",
                    sku.color_code if sku else "",
                    sku.sku_no if sku else "",
                    sku.image_url if sku else "",
                    sku.color_remark if sku else "",
                    product.remark,
                    output.title if output else "",
                    "/".join(output.main_image_tags) if output else "",
                    output.color_copy if output else "",
                ]
            )
    export_id = f"vipshop-copy-export-{uuid4().hex}.xlsx"
    file_path = export_dir / export_id
    workbook.save(file_path)
    return {"export_id": export_id, "filename": export_id, "path": str(file_path)}
