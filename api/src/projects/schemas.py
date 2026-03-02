from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.projects.models import ProjectStatus
from src.skills.schemas import SkillRead


class ProjectCreate(BaseModel):
    title: str
    description: str = ""
    deadline: datetime | None = None
    required_skill_ids: list[int] = []


class ProjectUpdate(BaseModel):
    title: str | None = None
    description: str | None = None
    status: ProjectStatus | None = None
    deadline: datetime | None = None
    required_skill_ids: list[int] | None = None


class ProjectRead(BaseModel):
    id: UUID
    company_id: UUID
    title: str
    description: str
    status: ProjectStatus
    deadline: datetime | None
    required_skills: list[SkillRead]
    created_at: datetime
    updated_at: datetime


class ProjectListRead(BaseModel):
    id: UUID
    company_id: UUID
    title: str
    status: ProjectStatus
    deadline: datetime | None
    required_skills: list[SkillRead]
    created_at: datetime
