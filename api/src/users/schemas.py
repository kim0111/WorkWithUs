from uuid import UUID

from pydantic import BaseModel

from src.users.models import UserRole


class UserRead(BaseModel):
    id: UUID
    email: str
    role: UserRole
    is_active: bool


class StudentProfileRead(BaseModel):
    first_name: str
    last_name: str
    university: str
    faculty: str
    year_of_study: int | None
    bio: str
    skills: list[str] = []


class CompanyProfileRead(BaseModel):
    company_name: str
    description: str
    website: str
    contact_person: str


class UserWithProfileRead(BaseModel):
    id: UUID
    email: str
    role: UserRole
    is_active: bool
    student_profile: StudentProfileRead | None = None
    company_profile: CompanyProfileRead | None = None


class StudentProfileUpdate(BaseModel):
    first_name: str | None = None
    last_name: str | None = None
    university: str | None = None
    faculty: str | None = None
    year_of_study: int | None = None
    bio: str | None = None
    skill_ids: list[int] | None = None


class CompanyProfileUpdate(BaseModel):
    company_name: str | None = None
    description: str | None = None
    website: str | None = None
    contact_person: str | None = None
