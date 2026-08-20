from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from db.database import Base

class ResearchTask(Base):
    __tablename__ = "research_tasks"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    project_id = Column(Integer, ForeignKey("research_projects.id"), nullable=False)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    assignee_id = Column(Integer, ForeignKey("users.id"), nullable=True)
    status = Column(String(50), default="TODO", nullable=False)
    priority = Column(String(50), default="MEDIUM", nullable=False)
    due_date = Column(DateTime, nullable=True)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)