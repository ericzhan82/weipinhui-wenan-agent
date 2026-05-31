from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import or_
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Product, ProductSku
from app.schemas import ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/api/products", tags=["products"])


@router.get("", response_model=list[ProductRead])
def list_products(
    keyword: str | None = Query(default=None),
    status: str | None = None,
    gender: str | None = None,
    season: str | None = None,
    db: Session = Depends(get_db),
):
    query = db.query(Product)
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
    return query.order_by(Product.updated_at.desc()).all()


@router.post("", response_model=ProductRead)
def create_product(payload: ProductCreate, db: Session = Depends(get_db)):
    data = payload.model_dump(exclude={"skus"})
    product = Product(**data)
    db.add(product)
    db.flush()
    for sku in payload.skus:
        db.add(ProductSku(product_id=product.id, **sku.model_dump()))
    db.commit()
    db.refresh(product)
    return product


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "商品不存在")
    return product


@router.put("/{product_id}", response_model=ProductRead)
def update_product(product_id: int, payload: ProductUpdate, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "商品不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(product, key, value)
    db.commit()
    db.refresh(product)
    return product


@router.delete("/{product_id}")
def delete_product(product_id: int, db: Session = Depends(get_db)):
    product = db.get(Product, product_id)
    if not product:
        raise HTTPException(404, "商品不存在")
    db.delete(product)
    db.commit()
    return {"deleted": True}
