from pydantic import BaseModel, Field, field_validator, ConfigDict
from typing import Optional
import re
from datetime import datetime
from app.utils.sanitizer import strip_all_tags


class RegisterRequest(BaseModel):
    phone: str = Field(..., min_length=11, max_length=20)
    password: str = Field(..., min_length=8, max_length=50)
    confirm_password: str = Field(..., min_length=8, max_length=50)
    nickname: Optional[str] = None
    role: str = "USER"

    @field_validator("phone")
    @classmethod
    def validate_phone(cls, v: str) -> str:
        if not re.match(r"^1[3-9]\d{9}$", v):
            raise ValueError("手机号格式不正确")
        return v

    @field_validator("password")
    @classmethod
    def validate_password_strength(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("密码长度至少8位")
        if not re.search(r"[a-z]", v):
            raise ValueError("密码必须包含小写字母")
        if not re.search(r"[A-Z]", v):
            raise ValueError("密码必须包含大写字母")
        if not re.search(r"\d", v):
            raise ValueError("密码必须包含数字")
        return v

    @field_validator("confirm_password")
    @classmethod
    def validate_confirm_password(cls, v: str, info) -> str:
        if "password" in info.data and v != info.data["password"]:
            raise ValueError("两次输入的密码不一致")
        return v

    @field_validator("nickname")
    @classmethod
    def sanitize_nickname(cls, v: Optional[str]) -> Optional[str]:
        """Strip all HTML tags from nickname (SEC-REFORM-07)."""
        if v is not None:
            return strip_all_tags(v)
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
    refresh_token: Optional[str] = None
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

    @field_validator("nickname")
    @classmethod
    def sanitize_nickname(cls, v: Optional[str]) -> Optional[str]:
        """Strip all HTML tags from nickname (SEC-REFORM-07)."""
        if v is not None:
            return strip_all_tags(v)
        return v
