from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.auth import AuthContext, get_workspace_context, require_workspace_write
from app.db import get_db
from app.models import Product, ProductSku
from app.schemas import ProductCreate, ProductRead, ProductUpdate
from app.services.copy_batch_service import product_context_ready, product_has_copy

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def list_products(
    keyword: str | None = Query(default=None),
    status: str | None = None,
    gender: str | None = None,
    season: str | None = None,
    context_status: str | None = None,
    copy_state: str | None = None,
    context: AuthContext = Depends(get_workspace_context),
    db: Session = Depends(get_db),
):
    query = db.query(Product).filter(Product.workspace_id == context.workspace_id)
    if keyword:
        like = f"%{keyword}%"
        query = query.filter(
            or_(
                Product.style_no.like(like),
                Product.product_no.like(like),
                Product.category_3.like(like),
                Product.category_4.like(like),
                Product.fba.like(like),
            )
        )
    if status:
        query = query.filter(Product.status == status)
    if gender:
        query = query.filter(Product.gender == gender)
    if season:
        query = query.filter(Product.season == season)
    products = query.order_by(Product.updated_at.desc()).all()
    if context_status == "ready":
        products = [product for product in products if product_context_ready(product)]
    elif context_status == "missing":
        products = [product for product in products if not product_context_ready(product)]
    if copy_state == "generated":
        products = [product for product in products if product_has_copy(product)]
    elif copy_state == "not_generated":
        products = [product for product in products if not product_has_copy(product)]
    return products


@router.post("", response_model=ProductRead)
def create_product(payload: ProductCreate, context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    data = payload.model_dump(exclude={"skus"})
    product = Product(**data, workspace_id=context.workspace_id)
    if product_context_ready(product):
        product.status = "ready"
    db.add(product)
    db.flush()
    for sku in payload.skus:
        db.add(ProductSku(product_id=product.id, **sku.model_dump()))
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, context: AuthContext = Depends(get_workspace_context), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product or product.workspace_id != context.workspace_id:
        raise HTTPException(404, "商品不存在")
    return product


@router.put("/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product or product.workspace_id != context.workspace_id:
        raise HTTPException(404, "商品不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(product_id: int, context: AuthContext = Depends(require_workspace_write), db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product or product.workspace_id != context.workspace_id:
        raise HTTPException(404, "商品不存在")
    db.delete(product)
    db.commit()
    return {"deleted": True}
