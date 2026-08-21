from datetime import datetime, timezone
from sqlalchemy import ( Column, Integer, String, Text,DateTime,ForeignKey,UniqueConstraint)
from sqlalchemy.orm import relationship
from db.database import Base


class ResearchProject(Base):
    __tablename__ = "research_projects"
    id = Column(Integer, primary_key=True, index=True, autoincrement=True)
    name = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id"), nullable=False)
    created_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    owner = relationship(
        "User", back_populates="owned_projects", foreign_keys=[owner_id]
    )
    members = relationship("ResearchMember", back_populates="project")
    tasks = relationship("ResearchTask", back_populates="project")


class ResearchMember(Base):
    __tablename__ = "research_members"
    project_id = Column(Integer, ForeignKey("research_projects.id"), primary_key=True)
    user_id = Column(Integer, ForeignKey("users.id"), primary_key=True)
    role = Column(String(50), nullable=False)
    joined_at = Column(
        DateTime, default=lambda: datetime.now(timezone.utc), nullable=False
    )

    __table_args__ = (
        UniqueConstraint("project_id", "user_id", name="uq_project_member"),
    )
    # Khai báo các mối quan hệ
    user = relationship("User", back_populates="project_memberships")
    project = relationship("ResearchProject", back_populates="members")
