from pydantic import BaseModel, Field, field_validator
from typing import Optional
from datetime import datetime

class TaskCreate(BaseModel):
    title: str = Field(..., min_length=1, max_length=255, description="Tiêu đề nhiệm vụ không được để trống")
    description: Optional[str] = Field(None, max_length=1000, description="Mô tả chi tiết nhiệm vụ")
    status: Optional[str] = Field("TODO", description="Trạng thái: TODO, IN_PROGRESS, DONE")
    priority: Optional[str] = Field("MEDIUM", description="Độ ưu tiên: LOW, MEDIUM, HIGH")
    assignee_id: Optional[int] = Field(None, gt=0, description="ID thành viên được giao việc")

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v not in ["TODO", "IN_PROGRESS", "DONE"]:
            raise ValueError("Status phải là một trong các giá trị: TODO, IN_PROGRESS, DONE")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v not in ["LOW", "MEDIUM", "HIGH"]:
            raise ValueError("Priority phải là một trong các giá trị: LOW, MEDIUM, HIGH")
        return v


class TaskUpdate(BaseModel):
    title: Optional[str] = Field(None, min_length=1, max_length=255)
    description: Optional[str] = Field(None, max_length=1000)
    status: Optional[str] = None
    priority: Optional[str] = None
    assignee_id: Optional[int] = Field(None, gt=0)

    @field_validator("status")
    @classmethod
    def validate_status(cls, v):
        if v is not None and v not in ["TODO", "IN_PROGRESS", "DONE"]:
            raise ValueError("Status phải là một trong các giá trị: TODO, IN_PROGRESS, DONE")
        return v

    @field_validator("priority")
    @classmethod
    def validate_priority(cls, v):
        if v is not None and v not in ["LOW", "MEDIUM", "HIGH"]:
            raise ValueError("Priority phải là một trong các giá trị: LOW, MEDIUM, HIGH")
        return v


# Đảm bảo có mặt class TaskResponse này để Router gọi import
class TaskResponse(BaseModel):
    id: int
    project_id: int
    title: str
    description: Optional[str] = None
    status: str
    priority: str
    assignee_id: Optional[int] = None
    created_at: Optional[datetime] = None

    class Config:
        from_attributes = True