from pathlib import Path
from uuid import uuid4

from openpyxl import Workbook
from sqlalchemy.orm import Session

from app.models import CopyBatch, CopyBatchItem, Product, Workspace

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
    "工作空间",
    "批量任务号",
    "批量状态",
    "失败原因",
]


def _write_product_row(sheet, product: Product, workspace: Workspace | None = None, batch_no: str = "", batch_status: str = "", error_message: str = "") -> None:
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
                workspace.name if workspace else "",
                batch_no,
                batch_status,
                error_message,
            ]
        )


def _base_workbook():
    workbook = Workbook()
    sheet = workbook.active
    sheet.title = "唯品文案导出"
    sheet.append(HEADERS)
    return workbook, sheet


def export_products(db: Session, storage_dir: str, keyword: str | None = None, workspace_id: int | None = None) -> dict:
    export_dir = Path(storage_dir) / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    query = db.query(Product)
    if workspace_id is not None:
        query = query.filter(Product.workspace_id == workspace_id)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(Product.style_no.like(like) | Product.product_no.like(like))
    products = query.order_by(Product.created_at.desc()).all()
    workspace = db.get(Workspace, workspace_id) if workspace_id else None
    workbook, sheet = _base_workbook()
    for product in products:
        _write_product_row(sheet, product, workspace=workspace)
    export_id = f"vipshop-copy-export-{uuid4().hex}.xlsx"
    file_path = export_dir / export_id
    workbook.save(file_path)
    return {"export_id": export_id, "filename": export_id, "path": str(file_path)}


def export_copy_batch(db: Session, storage_dir: str, batch: CopyBatch) -> dict:
    export_dir = Path(storage_dir) / "exports"
    export_dir.mkdir(parents=True, exist_ok=True)
    workspace = db.get(Workspace, batch.workspace_id)
    workbook, sheet = _base_workbook()
    items = (
        db.query(CopyBatchItem)
        .filter(CopyBatchItem.batch_id == batch.id, CopyBatchItem.status == "success")
        .order_by(CopyBatchItem.id.asc())
        .all()
    )
    for item in items:
        product = db.get(Product, item.product_id)
        if product:
            _write_product_row(
                sheet,
                product,
                workspace=workspace,
                batch_no=batch.batch_no,
                batch_status=item.status,
                error_message=item.error_message or "",
            )
    export_id = f"vipshop-copy-batch-{batch.batch_no}-{uuid4().hex}.xlsx"
    file_path = export_dir / export_id
    workbook.save(file_path)
    return {"export_id": export_id, "filename": export_id, "path": str(file_path)}
