from datetime import datetime
from sqlalchemy import Column, Integer, String, Text, DateTime, ForeignKey, UniqueConstraint
from db.database import Base

class ResearchProject(Base):
    __tablename__ = "research_projects"

    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=True)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(DateTime, default=datetime.utcnow, nullable=False)

class ResearchMember(Base):
    __tablename__ = "research_members"

    project_id = Column(Integer, ForeignKey("research_projects.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role = Column(String(50), nullable=False)
    joined_at = Column(DateTime, default=datetime.utcnow, nullable=False)

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member"),
    )