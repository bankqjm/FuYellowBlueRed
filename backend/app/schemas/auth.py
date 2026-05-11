from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
import re
from datetime import datetime


class RegisterRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=20)
    password: str = Field(..., min_length=6, max_length=50)
    nickname: Optional[str] = None
    role: str = "USER"

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v


class LoginRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=20)
    password: str = Field(...)

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v


class TokenResponse(BaseModel):
    model_config = ConfigDict(from_attributes=True)
    access_token: str
    token_type: str = "bearer"
    user_id: int
    role: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None


class UserInfo(BaseModel):
    model_config = ConfigDict(from_attributes=True, ser_json_timedelta="iso8601")
    id: int
    phone: str
    nickname: Optional[str] = None
    avatar: Optional[str] = None
    role: str
    status: int
    created_at: Optional[datetime] = None


class UpdateUserRequest(BaseModel):
    nickname: Optional[str] = None
    avatar: Optional[str] = None
