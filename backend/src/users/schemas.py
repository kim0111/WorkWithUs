from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from src.users.models import RoleEnum


class SkillOut(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    class Config:
        from_attributes = True


class UserBase(BaseModel):
    email: EmailStr
    username: str
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class UserResponse(UserBase):
    id: int
    role: RoleEnum
    is_active: bool
    is_blocked: bool
    skills: list[SkillOut] = []
    created_at: datetime
    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


class CompanyProfileCreate(BaseModel):
    company_name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None


class CompanyProfileResponse(CompanyProfileCreate):
    id: int
    user_id: int
    class Config:
        from_attributes = True


class StudentProfileCreate(BaseModel):
    university: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None


class StudentProfileResponse(StudentProfileCreate):
    id: int
    user_id: int
    rating: float
    completed_projects_count: int
    resume_url: Optional[str] = None
    class Config:
        from_attributes = True
