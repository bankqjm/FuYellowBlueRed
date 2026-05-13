from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Generic, TypeVar, List
from datetime import datetime

T = TypeVar("T")


class BaseSchema(BaseModel):
    model_config = ConfigDict(from_attributes=True)


class ResponseSchema(BaseSchema, Generic[T]):
    code: int = 0
    message: str = "success"
    data: Optional[T] = None


class PageParams(BaseSchema):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)


class PageResponse(BaseSchema, Generic[T]):
    items: List[T]
    total: int
    page: int
    page_size: int
