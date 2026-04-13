from datetime import datetime
from typing import Literal, Optional
from pydantic import BaseModel, Field
from src.projects.models import ProjectStatus
from src.users.schemas import SkillOut


class ProjectFileResponse(BaseModel):
    id: int
    filename: str
    object_name: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    file_type: str
    created_at: datetime

    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    max_participants: int = Field(default=1, ge=1)
    deadline: Optional[datetime] = None
    skill_ids: list[int] = []
    is_student_project: bool = False


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    max_participants: Optional[int] = None
    deadline: Optional[datetime] = None


class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str
    owner_id: int
    status: ProjectStatus
    max_participants: int
    deadline: Optional[datetime] = None
    is_student_project: bool
    required_skills: list[SkillOut] = []
    attachments: list[ProjectFileResponse] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    size: int
