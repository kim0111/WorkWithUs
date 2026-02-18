from datetime import datetime
from typing import Optional
from pydantic import BaseModel, EmailStr, Field
from app.models.models import RoleEnum, ApplicationStatus, ProjectStatus


# ── Auth ──────────────────────────────────────────────

class RegisterRequest(BaseModel):
    email: EmailStr
    username: str = Field(..., min_length=3, max_length=100)
    password: str = Field(..., min_length=6, max_length=128)
    full_name: Optional[str] = None
    role: RoleEnum = RoleEnum.student


class LoginRequest(BaseModel):
    username: str
    password: str


class TokenResponse(BaseModel):
    access_token: str
    refresh_token: str
    token_type: str = "bearer"


class RefreshTokenRequest(BaseModel):
    refresh_token: str


# ── Skills ────────────────────────────────────────────

class SkillBase(BaseModel):
    name: str
    category: Optional[str] = None


class SkillCreate(SkillBase):
    pass


class SkillResponse(SkillBase):
    id: int

    class Config:
        from_attributes = True


# ── User ──────────────────────────────────────────────

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
    skills: list[SkillResponse] = []
    created_at: datetime

    class Config:
        from_attributes = True


class UserUpdate(BaseModel):
    full_name: Optional[str] = None
    bio: Optional[str] = None
    avatar_url: Optional[str] = None


# ── Company Profile ───────────────────────────────────

class CompanyProfileBase(BaseModel):
    company_name: str
    industry: Optional[str] = None
    website: Optional[str] = None
    description: Optional[str] = None
    location: Optional[str] = None


class CompanyProfileCreate(CompanyProfileBase):
    pass


class CompanyProfileResponse(CompanyProfileBase):
    id: int
    user_id: int

    class Config:
        from_attributes = True


# ── Student Profile ───────────────────────────────────

class StudentProfileBase(BaseModel):
    university: Optional[str] = None
    major: Optional[str] = None
    graduation_year: Optional[int] = None
    gpa: Optional[float] = None
    resume_url: Optional[str] = None


class StudentProfileCreate(StudentProfileBase):
    pass


class StudentProfileResponse(StudentProfileBase):
    id: int
    user_id: int
    rating: float
    completed_projects_count: int

    class Config:
        from_attributes = True


# ── Project ───────────────────────────────────────────

class ProjectBase(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    max_participants: int = Field(default=1, ge=1)
    deadline: Optional[datetime] = None


class ProjectCreate(ProjectBase):
    skill_ids: list[int] = []
    is_student_project: bool = False


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    max_participants: Optional[int] = None
    deadline: Optional[datetime] = None


class ProjectResponse(ProjectBase):
    id: int
    owner_id: int
    status: ProjectStatus
    is_student_project: bool
    required_skills: list[SkillResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    size: int


# ── Application ───────────────────────────────────────

class ApplicationCreate(BaseModel):
    project_id: int
    cover_letter: Optional[str] = None


class ApplicationUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationResponse(BaseModel):
    id: int
    project_id: int
    applicant_id: int
    cover_letter: Optional[str]
    status: ApplicationStatus
    created_at: datetime

    class Config:
        from_attributes = True


# ── Portfolio ─────────────────────────────────────────

class PortfolioItemCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    project_url: Optional[str] = None
    image_url: Optional[str] = None


class PortfolioItemResponse(PortfolioItemCreate):
    id: int
    student_id: int
    created_at: datetime

    class Config:
        from_attributes = True


# ── Review ────────────────────────────────────────────

class ReviewCreate(BaseModel):
    reviewee_id: int
    project_id: int
    rating: float = Field(..., ge=1.0, le=5.0)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    reviewer_id: int
    reviewee_id: int
    project_id: int
    rating: float
    comment: Optional[str]
    created_at: datetime

    class Config:
        from_attributes = True


# ── Notification ──────────────────────────────────────

class NotificationResponse(BaseModel):
    id: int
    title: str
    message: Optional[str]
    is_read: bool
    created_at: datetime

    class Config:
        from_attributes = True


# ── Admin ─────────────────────────────────────────────

class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None
    role: Optional[RoleEnum] = None


class StatsResponse(BaseModel):
    total_users: int
    total_students: int
    total_companies: int
    total_projects: int
    total_applications: int
    active_projects: int
