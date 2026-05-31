from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.orm import Session

from app.db import get_db
from app.models import Product, ProductSku
from app.schemas import SkuCreate, SkuRead, SkuUpdate

router = APIRouter(prefix="/api", tags=["skus"])


@router.post("/products/{product_id}/skus", response_model=SkuRead)
def create_sku(product_id: int, payload: SkuCreate, db: Session = Depends(get_db)):
    if not db.get(Product, product_id):
        raise HTTPException(404, "商品不存在")
    sku = ProductSku(product_id=product_id, **payload.model_dump())
    db.add(sku)
    db.commit()
    db.refresh(sku)
    return sku


@router.put("/skus/{sku_id}", response_model=SkuRead)
def update_sku(sku_id: int, payload: SkuUpdate, db: Session = Depends(get_db)):
    sku = db.get(ProductSku, sku_id)
    if not sku:
        raise HTTPException(404, "SKC不存在")
    for key, value in payload.model_dump(exclude_unset=True).items():
        setattr(sku, key, value)
    db.commit()
    db.refresh(sku)
    return sku


@router.delete("/skus/{sku_id}")
def delete_sku(sku_id: int, db: Session = Depends(get_db)):
    sku = db.get(ProductSku, sku_id)
    if not sku:
        raise HTTPException(404, "SKC不存在")
    db.delete(sku)
    db.commit()
    return {"deleted": True}
