from pydantic import Field
from typing import Optional, List
from datetime import datetime
from app.schemas.base import BaseSchema


class CartItemCreate(BaseSchema):
    shop_id: int
    product_id: int
    quantity: int = Field(..., ge=1)


class CartItemUpdate(BaseSchema):
    quantity: Optional[int] = Field(None, ge=1)


class CartItemResponse(BaseSchema):
    id: int
    user_id: int
    shop_id: int
    product_id: int
    quantity: int
    created_at: Optional[datetime] = None
    product_name: Optional[str] = None
    product_image: Optional[str] = None
    product_price: Optional[float] = None
    shop_name: Optional[str] = None


class OrderItemResponse(BaseSchema):
    id: int
    order_id: int
    product_id: int
    product_name: str
    product_image: Optional[str] = None
    price: float
    quantity: int


class OrderCreate(BaseSchema):
    address_id: int
    shop_id: int
    remark: Optional[str] = None
    coupon_id: Optional[int] = None


class AddressInfo(BaseSchema):
    contact_name: str
    contact_phone: str
    address: str


class OrderResponse(BaseSchema):
    id: int
    order_no: str
    user_id: int
    shop_id: int
    rider_id: Optional[int] = None
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    phone: str
    remark: Optional[str] = None
    total_amount: float
    discount_amount: float = 0.0
    delivery_fee: float
    status: str
    reject_reason: Optional[str] = None
    created_at: Optional[datetime] = None
    updated_at: Optional[datetime] = None
    shop_name: Optional[str] = None
    shop_image: Optional[str] = None
    user_phone: Optional[str] = None
    user_nickname: Optional[str] = None
    items: Optional[List[OrderItemResponse]] = None
    address_info: Optional[AddressInfo] = None


class OrderQuery(BaseSchema):
    page: int = Field(default=1, ge=1)
    page_size: int = Field(default=20, ge=1, le=100)
    status: Optional[str] = None
