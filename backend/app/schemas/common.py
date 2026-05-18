from typing import Generic, TypeVar

from pydantic import BaseModel, Field

T = TypeVar("T")


class Paged(BaseModel, Generic[T]):
    items: list[T]
    total: int
    page: int
    page_size: int


class Message(BaseModel):
    detail: str = Field(..., description="Thông báo ngắn")


class HealthResponse(BaseModel):
    status: str = "ok"
    service: str = "backend"
