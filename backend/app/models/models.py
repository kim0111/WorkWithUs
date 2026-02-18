import enum
from datetime import datetime, timezone
from sqlalchemy import (
    Column, Integer, String, Text, ForeignKey, DateTime,
    Boolean, Enum, Float, Table
)
from sqlalchemy.orm import relationship
from app.database.session import Base


# ── Enums ──────────────────────────────────────────────

class RoleEnum(str, enum.Enum):
    student = "student"
    company = "company"
    committee = "committee"
    admin = "admin"


class ApplicationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    completed = "completed"


class ProjectStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"


# ── Association tables ─────────────────────────────────

user_skills = Table(
    "user_skills",
    Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)

project_skills = Table(
    "project_skills",
    Base.metadata,
    Column("project_id", Integer, ForeignKey("projects.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


# ── Models ─────────────────────────────────────────────

class User(Base):
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    email = Column(String(255), unique=True, index=True, nullable=False)
    username = Column(String(100), unique=True, index=True, nullable=False)
    hashed_password = Column(String(255), nullable=False)
    full_name = Column(String(255))
    role = Column(Enum(RoleEnum), nullable=False, default=RoleEnum.student)
    avatar_url = Column(String(500))
    bio = Column(Text)
    is_active = Column(Boolean, default=True)
    is_blocked = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    # Relationships
    skills = relationship("Skill", secondary=user_skills, back_populates="users", lazy="selectin")
    company_profile = relationship("CompanyProfile", back_populates="user", uselist=False, lazy="selectin")
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, lazy="selectin")
    projects = relationship("Project", back_populates="owner", lazy="selectin")
    applications = relationship("Application", back_populates="applicant", lazy="selectin")
    reviews_given = relationship("Review", foreign_keys="Review.reviewer_id", back_populates="reviewer", lazy="selectin")
    reviews_received = relationship("Review", foreign_keys="Review.reviewee_id", back_populates="reviewee", lazy="selectin")
    notifications = relationship("Notification", back_populates="user", lazy="selectin")


class CompanyProfile(Base):
    __tablename__ = "company_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    company_name = Column(String(255), nullable=False)
    industry = Column(String(255))
    website = Column(String(500))
    description = Column(Text)
    location = Column(String(255))

    user = relationship("User", back_populates="company_profile")


class StudentProfile(Base):
    __tablename__ = "student_profiles"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"), unique=True)
    university = Column(String(255))
    major = Column(String(255))
    graduation_year = Column(Integer)
    gpa = Column(Float)
    resume_url = Column(String(500))
    rating = Column(Float, default=0.0)
    completed_projects_count = Column(Integer, default=0)

    user = relationship("User", back_populates="student_profile")
    portfolio_items = relationship("PortfolioItem", back_populates="student", lazy="selectin")


class Skill(Base):
    __tablename__ = "skills"

    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(100))

    users = relationship("User", secondary=user_skills, back_populates="skills")
    projects = relationship("Project", secondary=project_skills, back_populates="required_skills")


class Project(Base):
    __tablename__ = "projects"

    id = Column(Integer, primary_key=True, index=True)
    title = Column(String(255), nullable=False)
    description = Column(Text, nullable=False)
    owner_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    status = Column(Enum(ProjectStatus), default=ProjectStatus.open)
    max_participants = Column(Integer, default=1)
    deadline = Column(DateTime(timezone=True))
    is_student_project = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    owner = relationship("User", back_populates="projects")
    required_skills = relationship("Skill", secondary=project_skills, back_populates="projects", lazy="selectin")
    applications = relationship("Application", back_populates="project", lazy="selectin")


class Application(Base):
    __tablename__ = "applications"

    id = Column(Integer, primary_key=True, index=True)
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    applicant_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    cover_letter = Column(Text)
    status = Column(Enum(ApplicationStatus), default=ApplicationStatus.pending)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))
    updated_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc), onupdate=lambda: datetime.now(timezone.utc))

    project = relationship("Project", back_populates="applications")
    applicant = relationship("User", back_populates="applications")


class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    project_url = Column(String(500))
    image_url = Column(String(500))
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    student = relationship("StudentProfile", back_populates="portfolio_items")


class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    reviewee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    rating = Column(Float, nullable=False)
    comment = Column(Text)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    reviewer = relationship("User", foreign_keys=[reviewer_id], back_populates="reviews_given")
    reviewee = relationship("User", foreign_keys=[reviewee_id], back_populates="reviews_received")


class Notification(Base):
    __tablename__ = "notifications"

    id = Column(Integer, primary_key=True, index=True)
    user_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    message = Column(Text)
    is_read = Column(Boolean, default=False)
    created_at = Column(DateTime(timezone=True), default=lambda: datetime.now(timezone.utc))

    user = relationship("User", back_populates="notifications")
