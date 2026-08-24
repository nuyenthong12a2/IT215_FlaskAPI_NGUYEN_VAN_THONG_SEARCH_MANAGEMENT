import re
from typing import Optional
from datetime import datetime
from pydantic import BaseModel, EmailStr, field_validator


class UserBase(BaseModel):
    email: EmailStr
    full_name: str

    @field_validator("email")
    def validate_email(cls, v: str) -> str:
        if not v.endswith("@gmail.com"):
            raise ValueError("Email phải có dạng địa chỉ là @gmail.com")
        return v

    @field_validator("full_name")
    def format_full_name(cls, v: str) -> str:
        return " ".join(v.strip().title().split())


class UserCreate(UserBase):
    password: str

    @field_validator("password")
    def validate_strong_password(cls, v: str) -> str:
        if len(v) < 8:
            raise ValueError("Mật khẩu phải có ít nhất 8 ký tự")
        if not re.search(r"[A-Z]", v):
            raise ValueError("Mật khẩu phải chứa ít nhất một chữ cái viết hoa")
        if not re.search(r"[a-z]", v):
            raise ValueError("Mật khẩu phải chứa ít nhất một chữ cái viết thường")
        if not re.search(r"\d", v):
            raise ValueError("Mật khẩu phải chứa ít nhất một chữ số")
        if not re.search(r"[!@#$%^&*(),.?\":{}|<>]", v):
            raise ValueError("Mật khẩu phải chứa ít nhất một ký tự đặc biệt")
        return v


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    is_active: Optional[bool] = None

    @field_validator("full_name")
    def format_full_name(cls, v: Optional[str]) -> Optional[str]:
        if v is not None:
            return " ".join(v.strip().title().split())
        return v

    class Config:
        from_attributes = True


class UserResponse(BaseModel):
    id: int
    email: EmailStr
    full_name: str
    role: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True
