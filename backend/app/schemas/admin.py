from pydantic import BaseModel, Field


class AdminStatsResponse(BaseModel):
    product_count: int = Field(..., description="Số sản phẩm")
    review_count: int = Field(..., description="Số đánh giá")
    aspect_count: int = Field(..., description="Số bản ghi aspect–sentiment")
    pending_analysis: int = Field(..., description="Đánh giá chưa phân tích xong")
