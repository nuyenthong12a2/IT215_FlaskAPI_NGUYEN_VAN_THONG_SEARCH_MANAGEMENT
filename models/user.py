from datetime import datetime,timezone
from sqlalchemy import Column, Integer, String, Boolean, DateTime
from sqlalchemy.orm import relationship
from db.database import Base
 
 
class User(Base):
    __tablename__ = "users"
 
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    email = Column(String(255), unique=True, nullable=False, index=True)
    password_hash = Column(String(255), nullable=False)
    full_name = Column(String(255), nullable=False)
    role = Column(String(50), default="USER", nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime, default=lambda:datetime.now(timezone.utc), nullable=False)
 
    # 1 user có thể là owner của nhiều project 
    owned_projects = relationship(
        "ResearchProject",
        back_populates="owner",
        foreign_keys="[ResearchProject.owner_id]",
    )
 
    # 1 user có thể tham gia nhiều project qua bảng trung gian research_members
    project_memberships = relationship( "ResearchMember", back_populates="user")
 
    # 1 user có thể được giao nhiều task (User.id <- ResearchTask.assignee_id)
    assigned_tasks = relationship( "ResearchTask", back_populates="assignee" )
 