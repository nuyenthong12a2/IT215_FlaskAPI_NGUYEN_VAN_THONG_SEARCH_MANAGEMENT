from datetime import datetime
import re
from typing import Optional
from pydantic import BaseModel, Field, field_validator


class ProjectBase(BaseModel):
    name: Optional[str] = Field(None, min_length=3, max_length=200)
    description: Optional[str] = Field(None, max_length=1000)

    @field_validator("name")
    @classmethod
    def validate_name(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        cleaned_name = v.strip()
        if not cleaned_name:
            raise ValueError("Tên đề tài nghiên cứu không được để trống hoặc chứa toàn khoảng trắng!")
        
        # Chặn trường hợp chỉ chứa toàn số hoặc toàn ký tự đặc biệt
        if not re.search(r'[a-zA-ZÀ-ỹ]', cleaned_name):
            raise ValueError("Tên đề tài phải chứa ít nhất ký tự chữ cái hợp lệ, không được chỉ có số hoặc ký tự đặc biệt!")
            
        return cleaned_name

    @field_validator("description")
    @classmethod
    def validate_description(cls, v: Optional[str]) -> Optional[str]:
        if v is None:
            return v
        
        cleaned_desc = v.strip()
        # Nếu người dùng nhập description mà toàn khoảng trắng thì ép về None hoặc báo lỗi
        if cleaned_desc == "":
            return None
            
        # Kiểm tra nếu description có nội dung thì cũng phải chứa ít nhất một chữ cái hoặc số (chặn trường hợp gõ toàn "@@@")
        if not re.search(r'[a-zA-Z0-9À-ỹ]', cleaned_desc):
            raise ValueError("Mô tả đề tài phải có nội dung hợp lệ, không được chỉ chứa ký tự đặc biệt!")
            
        return cleaned_desc


class ProjectCreate(ProjectBase):
    name: str = Field(..., min_length=3, max_length=200)


class ProjectResponse(BaseModel):
    id: int
    name: str
    description: Optional[str] = None
    owner_id: int
    created_at: datetime

    class Config:
        from_attributes = True


class MemberResponse(BaseModel):
    project_id: int
    user_id: int
    role: str
    joined_at: datetime

    class Config:
        from_attributes = True


class ProjectUpdate(ProjectBase):
    pass