from pydantic import BaseModel, Field
from typing import Optional


class AddressCreate(BaseModel):
    contact_name: str = Field(..., min_length=1, max_length=50)
    contact_phone: str = Field(..., min_length=11, max_length=20)
    address: str = Field(..., min_length=1, max_length=255)
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: int = 0


class AddressUpdate(BaseModel):
    contact_name: Optional[str] = None
    contact_phone: Optional[str] = None
    address: Optional[str] = None
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: Optional[int] = None


class AddressResponse(BaseModel):
    id: int
    user_id: int
    contact_name: str
    contact_phone: str
    address: str
    latitude: Optional[float] = None
    longitude: Optional[float] = None
    is_default: int
    created_at: Optional[str] = None
