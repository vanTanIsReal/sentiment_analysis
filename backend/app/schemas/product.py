from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class ProductBase(BaseModel):
    name: str = Field(..., max_length=512)
    brand: str | None = None
    url: str
    price: float | None = None
    image_url: str | None = None
    external_id: str | None = None


class ProductCreate(ProductBase):
    pass


class ProductRead(ProductBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    created_at: datetime


class ProductUpdate(BaseModel):
    name: str | None = Field(None, max_length=512)
    brand: str | None = None
    url: str | None = None
    price: float | None = None
    image_url: str | None = None
    external_id: str | None = None
