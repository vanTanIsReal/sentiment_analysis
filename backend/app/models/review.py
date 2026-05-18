"""ORM model: đánh giá khách hàng."""

from datetime import datetime

from sqlalchemy import DateTime, ForeignKey, Integer, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Review(Base):
    __tablename__ = "reviews"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    product_id: Mapped[int] = mapped_column(ForeignKey("products.id", ondelete="CASCADE"), index=True)
    author: Mapped[str | None] = mapped_column(String(256), nullable=True)
    rating: Mapped[int | None] = mapped_column(Integer, nullable=True)
    content: Mapped[str] = mapped_column(Text)
    source: Mapped[str] = mapped_column(String(64), default="tgdd", server_default="tgdd")
    reviewed_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True), nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    analysis_status: Mapped[str] = mapped_column(
        String(32), default="pending", server_default="pending", index=True
    )

    product: Mapped["Product"] = relationship("Product", back_populates="reviews")
    aspects: Mapped[list["AspectSentiment"]] = relationship(
        "AspectSentiment", back_populates="review", cascade="all, delete-orphan"
    )
