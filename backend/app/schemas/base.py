from decimal import Decimal
from pydantic import BaseModel, Field, ConfigDict
from typing import Optional, Generic, TypeVar, List, Annotated
from pydantic.functional_serializers import PlainSerializer

T = TypeVar("T")

# Serialize Decimal as float for JSON API compatibility
DecimalField = Annotated[
    Decimal,
    PlainSerializer(lambda x: float(x), return_type=float, when_used="json"),
]


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
