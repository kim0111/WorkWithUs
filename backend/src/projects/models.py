import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, Boolean, Enum, Table
from sqlalchemy.orm import relationship
from src.database.postgres import Base


class ProjectStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"


project_skills = Table(
    "project_skills", Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    status = Column(Enum(ProjectStatus), default=ProjectStatus.open)
    max_participants = Column(Integer, default=1)
    deadline = Column(DateTime)
    is_student_project = Column(Boolean, default=False)
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(),
                        onupdate=lambda: datetime.utcnow())

    owner = relationship("User", back_populates="owned_projects")
    required_skills = relationship("Skill", secondary=project_skills, back_populates="projects", lazy="selectin")
    applications = relationship("Application", back_populates="project", lazy="selectin")
    attachments = relationship("ProjectFile", back_populates="project", lazy="selectin")


class ProjectFile(Base):
    __tablename__ = "project_files"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    uploader_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    filename = Column(String(500), nullable=False)
    object_name = Column(String(500), nullable=False)  # MinIO key
    file_size = Column(Integer)
    content_type = Column(String(255))
    file_type = Column(String(50), default="attachment")  # attachment | submission
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    project = relationship("Project", back_populates="attachments")
