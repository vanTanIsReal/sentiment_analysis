"""ORM model: kết quả phân tích (aspect + sentiment) từ AI."""

from sqlalchemy import Float, ForeignKey, String, Text
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class AspectSentiment(Base):
    __tablename__ = "aspect_sentiments"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    review_id: Mapped[int] = mapped_column(ForeignKey("reviews.id", ondelete="CASCADE"), index=True)
    aspect: Mapped[str] = mapped_column(String(128), index=True)
    sentiment: Mapped[str] = mapped_column(String(32))
    confidence: Mapped[float | None] = mapped_column(Float, nullable=True)
    quote: Mapped[str | None] = mapped_column(Text, nullable=True)

    review: Mapped["Review"] = relationship("Review", back_populates="aspects")
