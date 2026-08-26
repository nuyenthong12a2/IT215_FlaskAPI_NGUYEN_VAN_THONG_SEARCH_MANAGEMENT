from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey
from sqlalchemy.orm import relationship
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
    
    # Không lambda, truyền thẳng datetime.now cực kỳ sạch sẽ
    created_at = Column(DateTime, default=datetime.now, nullable=False)
 
    project = relationship("ResearchProject", back_populates="tasks")
    assignee = relationship("User", back_populates="assigned_tasks")