"""API sản phẩm điện thoại."""

from fastapi import APIRouter, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import Product
from app.schemas import Paged, ProductCreate, ProductRead, ProductUpdate

router = APIRouter(prefix="/products", tags=["products"])


@router.get("", response_model=Paged[ProductRead])
def list_products(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(20, ge=1, le=100),
    q: str | None = Query(None, description="Tìm theo tên/brand"),
) -> Paged[ProductRead]:
    filters = []
    if q:
        like = f"%{q}%"
        filters.append(
            (Product.name.ilike(like)) | (Product.brand.isnot(None) & (Product.brand.ilike(like)))
        )
    count_stmt = select(func.count()).select_from(Product)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = db.scalar(count_stmt)

    stmt = select(Product)
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.order_by(Product.created_at.desc()).offset((page - 1) * page_size).limit(page_size)
    rows = list(db.scalars(stmt).all())
    return Paged(
        items=rows,
        total=int(total or 0),
        page=page,
        page_size=page_size,
    )


@router.get("/{product_id}", response_model=ProductRead)
def get_product(product_id: int, db: Session = Depends(get_db)) -> Product:
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    return p


@router.post("", response_model=ProductRead, status_code=201)
def create_product(body: ProductCreate, db: Session = Depends(get_db)) -> Product:
    prod = Product(**body.model_dump())
    db.add(prod)
    db.commit()
    db.refresh(prod)
    return prod


@router.patch("/{product_id}", response_model=ProductRead)
def update_product(
    product_id: int, body: ProductUpdate, db: Session = Depends(get_db)
) -> Product:
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    for k, v in body.model_dump(exclude_unset=True).items():
        setattr(p, k, v)
    db.commit()
    db.refresh(p)
    return p


@router.delete("/{product_id}", status_code=204)
def delete_product(product_id: int, db: Session = Depends(get_db)) -> None:
    p = db.get(Product, product_id)
    if not p:
        raise HTTPException(status_code=404, detail="Không tìm thấy sản phẩm")
    db.delete(p)
    db.commit()
