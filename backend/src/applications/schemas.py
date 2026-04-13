from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from src.applications.models import ApplicationStatus


class ApplicationCreate(BaseModel):
    project_id: int
    cover_letter: Optional[str] = None


class ApplicationUpdateStatus(BaseModel):
    status: ApplicationStatus
    note: Optional[str] = None


class StatusHistoryEntry(BaseModel):
    status: str
    timestamp: datetime
    actor_id: Optional[int] = None
    actor_name: str
    note: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    project_id: int
    applicant_id: int
    cover_letter: Optional[str] = None
    status: ApplicationStatus
    submission_note: Optional[str] = None
    revision_note: Optional[str] = None
    status_history: list[StatusHistoryEntry] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
