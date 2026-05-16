
from pydantic import Field
from typing import Optional, List
from datetime import datetime
from app.schemas.base import BaseSchema


class ShopCreate(BaseSchema):
    name: str = Field(..., min_length=2, max_length=100)
    logo: Optional[str] = None
    address: str = Field(..., min_length=5, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    business_hours: Optional[str] = None
    notice: Optional[str] = None


class ShopUpdate(BaseSchema):
    name: Optional[str] = Field(None, min_length=2, max_length=100)
    logo: Optional[str] = None
    address: Optional[str] = Field(None, min_length=5, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    business_hours: Optional[str] = None
    notice: Optional[str] = None
    min_order_amount: Optional[float] = None
    delivery_fee: Optional[float] = None
    delivery_time: Optional[str] = None
    discounts: Optional[str] = None


class ShopInfo(BaseSchema):
    id: int
    user_id: int
    name: str
    logo: Optional[str] = None
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    business_hours: Optional[str] = None
    notice: Optional[str] = None
    rating: float
    status: int
    monthly_sales: int = 0
    min_order_amount: float = 20.0
    delivery_fee: float = 3.0
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
    notice: Optional[str] = None
    rating: float
    status: int
    monthly_sales: int = 0
    min_order_amount: float = 20.0
    delivery_fee: float = 3.0
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
    price: float = Field(..., ge=0)
    original_price: Optional[float] = None
    description: Optional[str] = None
    stock: int = Field(0, ge=0)


class ProductUpdate(BaseSchema):
    category_id: Optional[int] = None
    name: Optional[str] = Field(None, min_length=1, max_length=100)
    image: Optional[str] = None
    price: Optional[float] = Field(None, ge=0)
    original_price: Optional[float] = None
    description: Optional[str] = None
    stock: Optional[int] = Field(None, ge=0)
    status: Optional[int] = None


class ProductInfo(BaseSchema):
    id: int
    shop_id: int
    category_id: Optional[int] = None
    name: str
    image: Optional[str] = None
    price: float
    original_price: Optional[float] = None
    description: Optional[str] = None
    stock: int
    sales: int
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


class ShopReview(BaseSchema):
    pass

