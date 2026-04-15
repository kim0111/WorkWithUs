from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from src.applications.models import ApplicationStatus, ApplicationInitiator


class ApplicationCreate(BaseModel):
    project_id: int
    cover_letter: Optional[str] = None


class ApplicationInviteCreate(BaseModel):
    project_id: int
    student_id: int
    message: Optional[str] = Field(None, max_length=2000)


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
    initiator: ApplicationInitiator
    submission_note: Optional[str] = None
    revision_note: Optional[str] = None
    status_history: list[StatusHistoryEntry] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
