from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from src.applications.models import ApplicationStatus


class ApplicationCreate(BaseModel):
    cover_letter: str = ""


class ApplicationStatusUpdate(BaseModel):
    status: ApplicationStatus


class ApplicationRead(BaseModel):
    id: UUID
    project_id: UUID
    student_id: UUID
    cover_letter: str
    status: ApplicationStatus
    created_at: datetime
    updated_at: datetime
