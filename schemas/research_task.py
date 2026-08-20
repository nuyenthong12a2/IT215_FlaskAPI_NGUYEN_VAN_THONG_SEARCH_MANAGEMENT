from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class TaskBase(BaseModel):
    title: str
    description: Optional[str] = None
    priority: str = "MEDIUM"
    status: str = "TODO"
    due_date: Optional[datetime] = None


class TaskCreate(TaskBase):
    assignee_id: Optional[int] = None


class TaskResponse(TaskBase):
    id: int
    project_id: int
    assignee_id: Optional[int]
    created_at: datetime

    class Config:
        from_attributes = True


class TaskUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    priority: Optional[str] = None
    due_date: Optional[datetime] = None
    assignee_id: Optional[int] = None

    class Config:
        from_attributes = True
