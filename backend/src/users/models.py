import enum
from datetime import datetime, timezone
from sqlalchemy import Column, Integer, String, Text, Boolean, Enum, DateTime, Float, Table, ForeignKey
from sqlalchemy.orm import relationship
from src.database.postgres import Base


class RoleEnum(str, enum.Enum):
    student = "student"
    company = "company"
    committee = "committee"
    admin = "admin"


user_skills = Table(
    "user_skills", Base.metadata,
    Column("user_id", Integer, ForeignKey("users.id", ondelete="CASCADE"), primary_key=True),
    Column("skill_id", Integer, ForeignKey("skills.id", ondelete="CASCADE"), primary_key=True),
)


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
    created_at = Column(DateTime, default=lambda: datetime.utcnow())
    updated_at = Column(DateTime, default=lambda: datetime.utcnow(),
                            onupdate=lambda: datetime.utcnow())

    skills = relationship("Skill", secondary=user_skills, back_populates="users", lazy="selectin")
    company_profile = relationship("CompanyProfile", back_populates="user", uselist=False, lazy="selectin")
    student_profile = relationship("StudentProfile", back_populates="user", uselist=False, lazy="selectin")
    owned_projects = relationship("Project", back_populates="owner", lazy="selectin")
    applications = relationship("Application", back_populates="applicant", lazy="selectin")


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
