from datetime import datetime

from pydantic import BaseModel, ConfigDict, Field


class AspectSentimentRead(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    aspect: str
    sentiment: str
    confidence: float | None
    quote: str | None


class ReviewBase(BaseModel):
    author: str | None = Field(None, max_length=256)
    rating: int | None = Field(None, ge=1, le=5)
    content: str
    source: str = Field(default="tgdd", max_length=64)
    reviewed_at: datetime | None = None


class ReviewCreate(ReviewBase):
    product_id: int


class ReviewRead(ReviewBase):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    created_at: datetime
    analysis_status: str
    aspects: list[AspectSentimentRead] = Field(default_factory=list)


class ReviewListItem(BaseModel):
    model_config = ConfigDict(from_attributes=True)

    id: int
    product_id: int
    author: str | None
    rating: int | None
    content: str
    source: str
    reviewed_at: datetime | None
    created_at: datetime
    analysis_status: str
