"""API cho trang quản trị (thống kê, báo cáo)."""

from fastapi import APIRouter, Depends
from sqlalchemy import func, select
from sqlalchemy.orm import Session

from app.db.database import get_db
from app.models import AspectSentiment, Product, Review
from app.schemas import AdminStatsResponse

router = APIRouter(prefix="/admin", tags=["admin"])


@router.get("/stats", response_model=AdminStatsResponse)
def get_stats(db: Session = Depends(get_db)) -> AdminStatsResponse:
    n_products = db.scalar(select(func.count()).select_from(Product)) or 0
    n_reviews = db.scalar(select(func.count()).select_from(Review)) or 0
    n_aspects = db.scalar(select(func.count()).select_from(AspectSentiment)) or 0
    pending = db.scalar(
        select(func.count())
        .select_from(Review)
        .where(Review.analysis_status == "pending")
    ) or 0
    return AdminStatsResponse(
        product_count=int(n_products),
        review_count=int(n_reviews),
        aspect_count=int(n_aspects),
        pending_analysis=int(pending),
    )
