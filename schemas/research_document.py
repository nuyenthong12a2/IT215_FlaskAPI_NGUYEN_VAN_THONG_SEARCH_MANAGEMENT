from pydantic import BaseModel
from datetime import datetime


class DocumentResponse(BaseModel):
    id: int
    project_id: int
    file_name: str
    file_path: str
    uploaded_by: int
    created_at: datetime

    class Config:
        from_attributes = True
