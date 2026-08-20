from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ProjectBase(BaseModel):
    name: str
    description: Optional[str] = None


class ProjectCreate(ProjectBase):
    pass


class ProjectResponse(ProjectBase):
    id: int
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


class ProjectUpdate(BaseModel):
    name: Optional[str] = None
    description: Optional[str] = None

    class Config:
        from_attributes = True
