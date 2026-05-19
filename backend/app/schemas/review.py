from pydantic import Field
from typing import Optional, List
from datetime import datetime
from app.schemas.base import BaseSchema


class ReviewCreate(BaseSchema):
    order_id: int
    shop_rating: int = Field(..., ge=1, le=5)
    rider_rating: Optional[int] = Field(None, ge=1, le=5)
    content: Optional[str] = None
    images: Optional[List[str]] = Field(default_factory=list)


class ReviewResponse(BaseSchema):
    id: int
    order_id: int
    user_id: int
    shop_id: int
    rider_id: Optional[int] = None
    shop_rating: int
    rider_rating: Optional[int] = None
    content: Optional[str] = None
    images: Optional[List[str]] = Field(default_factory=list)
    created_at: Optional[datetime] = None
    user_nickname: Optional[str] = None
