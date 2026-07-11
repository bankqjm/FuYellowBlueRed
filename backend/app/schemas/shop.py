
from decimal import Decimal
from pydantic import Field, field_validator
from typing import Optional, List
from datetime import datetime
from app.schemas.base import BaseSchema, DecimalField
from app.utils.sanitizer import strip_all_tags, sanitize_limited_html, strip_dangerous_content


class ShopCreate(BaseSchema):
    name: str = Field(..., min_length=2, max_length=100)
    logo: Optional[str] = None
    address: str = Field(..., min_length=5, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    business_hours: Optional[str] = None
    business_days: Optional[str] = None
    notice: Optional[str] = None

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """Strip dangerous HTML from shop name (SEC-REFORM-07)."""
        return strip_dangerous_content(v)

    @field_validator("notice")
    @classmethod
    def sanitize_notice(cls, v: Optional[str]) -> Optional[str]:
        """Allow limited safe HTML in shop notice (SEC-REFORM-07)."""
        if v is not None:
            return sanitize_limited_html(v)
        return v


class ShopUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    logo: Optional[str] = None
    address: Optional[str] = Field(None, min_length=5, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    business_hours: Optional[str] = None
    business_days: Optional[str] = None
    notice: Optional[str] = None
    min_order_amount: Optional[DecimalField] = None
    delivery_fee: Optional[DecimalField] = None
    delivery_time: Optional[str] = None
    discounts: Optional[str] = None

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        """Strip dangerous HTML from shop name (SEC-REFORM-07)."""
        if v is not None:
            return strip_dangerous_content(v)
        return v

    @field_validator("notice")
    @classmethod
    def sanitize_notice(cls, v: Optional[str]) -> Optional[str]:
        """Allow limited safe HTML in shop notice (SEC-REFORM-07)."""
        if v is not None:
            return sanitize_limited_html(v)
        return v


class ShopInfo(BaseSchema):
    id: int
    user_id: int
    name: str
    logo: Optional[str] = None
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    business_hours: Optional[str] = None
    business_days: Optional[str] = None
    notice: Optional[str] = None
    rating: float
    status: int
    monthly_sales: int = 0
    min_order_amount: DecimalField = Decimal("20.00")
    delivery_fee: DecimalField = Decimal("3.00")
    delivery_time: str = "30分钟"
    discounts: Optional[str] = None
    created_at: datetime
    updated_at: datetime


class ShopDetail(BaseSchema):
    id: int
    user_id: int
    name: str
    logo: Optional[str] = None
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    business_hours: Optional[str] = None
    business_days: Optional[str] = None
    notice: Optional[str] = None
    rating: float
    status: int
    monthly_sales: int = 0
    min_order_amount: DecimalField = Decimal("20.00")
    delivery_fee: DecimalField = Decimal("3.00")
    delivery_time: str = "30分钟"
    discounts: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    categories: Optional[List["CategoryInfo"]] = None


class CategoryCreate(BaseSchema):
    shop_id: int
    name: str = Field(..., min_length=1, max_length=50)
    sort_order: Optional[int] = 0


class CategoryUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=1, max_length=50)
    sort_order: Optional[int] = None


class CategoryInfo(BaseSchema):
    id: int
    shop_id: int
    name: str
    sort_order: int
    created_at: datetime
    products: Optional[List["ProductInfo"]] = None


class ProductCreate(BaseSchema):
    shop_id: int
    category_id: Optional[int] = None
    name: str = Field(..., min_length=1, max_length=100)
    image: Optional[str] = None
    price: DecimalField = Field(..., ge=0)
    original_price: Optional[DecimalField] = None
    description: Optional[str] = None
    stock: int = Field(0, ge=0)

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: str) -> str:
        """Strip dangerous HTML from product name (SEC-REFORM-07)."""
        return strip_dangerous_content(v)

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        """Allow limited safe HTML in product description (SEC-REFORM-07)."""
        if v is not None:
            return sanitize_limited_html(v)
        return v


class ProductUpdate(BaseSchema):
    category_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    image: Optional[str] = None
    price: Optional[DecimalField] = Field(None, ge=0)
    original_price: Optional[DecimalField] = None
    description: Optional[str] = None
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[int] = None

    @field_validator("name")
    @classmethod
    def sanitize_name(cls, v: Optional[str]) -> Optional[str]:
        """Strip dangerous HTML from product name (SEC-REFORM-07)."""
        if v is not None:
            return strip_dangerous_content(v)
        return v

    @field_validator("description")
    @classmethod
    def sanitize_description(cls, v: Optional[str]) -> Optional[str]:
        """Allow limited safe HTML in product description (SEC-REFORM-07)."""
        if v is not None:
            return sanitize_limited_html(v)
        return v


class ProductInfo(BaseSchema):
    id: int
    shop_id: int
    category_id: Optional[int] = None
    name: str
    image: Optional[str] = None
    price: DecimalField
    original_price: Optional[DecimalField] = None
    description: Optional[str] = None
    stock: int
    sales: int
    tags: Optional[str] = None
    rating: float = 0.0
    status: int
    created_at: datetime
    updated_at: datetime


class ShopListQuery(BaseSchema):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    keyword: Optional[str] = None
    status: Optional[int] = None


class ProductListQuery(BaseSchema):
    page: int = Field(1, ge=1)
    page_size: int = Field(20, ge=1, le=100)
    keyword: Optional[str] = None
    category_id: Optional[int] = None
    status: Optional[int] = None
    min_price: Optional[float] = None
    max_price: Optional[float] = None
    sort_by: Optional[str] = None  # price, sales, rating


class ShopReview(BaseSchema):
    pass
