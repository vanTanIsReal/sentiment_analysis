"""API đánh giá / bình luận từ khách hàng."""

from fastapi import APIRouter, BackgroundTasks, Depends, HTTPException, Query
from sqlalchemy import func, select
from sqlalchemy.orm import Session, selectinload

from app.db.database import get_db
from app.models import Product, Review
from app.schemas import Paged, ReviewCreate, ReviewListItem, ReviewRead
from app.services import trigger_review_analysis_sync

router = APIRouter(prefix="/reviews", tags=["reviews"])


@router.get("", response_model=Paged[ReviewListItem])
def list_reviews(
    db: Session = Depends(get_db),
    page: int = Query(1, ge=1),
    page_size: int = Query(50, ge=1, le=200),
    product_id: int | None = Query(None),
    status: str | None = Query(None, description="pending|done|error"),
) -> Paged[ReviewListItem]:
    filters = []
    if product_id is not None:
        filters.append(Review.product_id == product_id)
    if status:
        filters.append(Review.analysis_status == status)

    count_stmt = select(func.count()).select_from(Review)
    if filters:
        count_stmt = count_stmt.where(*filters)
    total = db.scalar(count_stmt)

    stmt = select(Review)
    if filters:
        stmt = stmt.where(*filters)
    stmt = stmt.order_by(Review.created_at.desc()).offset((page - 1) * page_size).limit(page_size)

    rows = list(db.scalars(stmt).all())
    return Paged(
        items=rows,
        total=int(total or 0),
        page=page,
        page_size=page_size,
    )


@router.get("/{review_id}", response_model=ReviewRead)
def get_review(review_id: int, db: Session = Depends(get_db)) -> Review:
    r = db.scalar(
        select(Review)
        .options(selectinload(Review.aspects))
        .where(Review.id == review_id)
    )
    if not r:
        raise HTTPException(status_code=404, detail="Không tìm thấy đánh giá")
    return r


@router.post("", response_model=ReviewRead, status_code=201)
def create_review(
    body: ReviewCreate,
    background_tasks: BackgroundTasks,
    db: Session = Depends(get_db),
    trigger_analyze: bool = Query(True, description="Gọi AI worker sau khi tạo"),
) -> Review:
    if not db.get(Product, body.product_id):
        raise HTTPException(status_code=400, detail="product_id không tồn tại")
    rev = Review(**body.model_dump())
    db.add(rev)
    db.commit()
    db.refresh(rev)

    if trigger_analyze:
        background_tasks.add_task(trigger_review_analysis_sync, rev.id)

    loaded = db.scalar(
        select(Review).options(selectinload(Review.aspects)).where(Review.id == rev.id)
    )
    assert loaded is not None
    return loaded
