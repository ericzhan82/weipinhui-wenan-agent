from sqlalchemy.orm import Session

from app.models import HistoryCase, Product


def save_history_case(db: Session, product_id: int, reason: str, operator_name: str) -> HistoryCase:
    product = db.get(Product, product_id)
    if not product:
        raise ValueError("商品不存在")
    if not product.copy_output:
        raise ValueError("商品还没有可沉淀的文案")
    case = HistoryCase(
        product_id=product.id,
        style_no=product.style_no,
        category_3=product.category_3,
        category_4=product.category_4,
        age_range=product.age_range,
        gender=product.gender,
        season=product.season,
        scene=product.scene,
        fba=product.fba,
        title=product.copy_output.title,
        main_image_tags=product.copy_output.main_image_tags,
        color_copy=product.copy_output.color_copy,
        reason=reason,
        created_by=operator_name,
    )
    db.add(case)
    db.commit()
    db.refresh(case)
    return case
