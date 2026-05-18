"""ORM model: sản phẩm điện thoại."""

from datetime import datetime

from sqlalchemy import DateTime, Float, String, Text, func
from sqlalchemy.orm import Mapped, mapped_column, relationship

from app.db.database import Base


class Product(Base):
    __tablename__ = "products"

    id: Mapped[int] = mapped_column(primary_key=True, autoincrement=True)
    external_id: Mapped[str | None] = mapped_column(String(128), unique=True, nullable=True)
    name: Mapped[str] = mapped_column(String(512), index=True)
    brand: Mapped[str | None] = mapped_column(String(128), nullable=True, index=True)
    url: Mapped[str] = mapped_column(Text, unique=True)
    price: Mapped[float | None] = mapped_column(Float, nullable=True)
    image_url: Mapped[str | None] = mapped_column(Text, nullable=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())

    reviews: Mapped[list["Review"]] = relationship(
        "Review", back_populates="product", cascade="all, delete-orphan"
    )
