from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from src.core.dependencies import get_current_user
from src.core.email import send_application_status_email, send_new_application_email, send_submission_email
from src.core.activity import log_activity
from src.users.models import User, RoleEnum
from src.projects.models import Project
from src.applications.models import Application, ApplicationStatus


# -- Schemas --

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


# -- Transition validation --

VALID_TRANSITIONS = {
    ApplicationStatus.pending: [ApplicationStatus.accepted, ApplicationStatus.rejected],
    ApplicationStatus.accepted: [ApplicationStatus.in_progress],
    ApplicationStatus.in_progress: [ApplicationStatus.submitted],
    ApplicationStatus.submitted: [ApplicationStatus.approved, ApplicationStatus.revision_requested],
    ApplicationStatus.revision_requested: [ApplicationStatus.submitted],
    ApplicationStatus.approved: [ApplicationStatus.completed],
}


def _append_history(app: Application, status: str, actor: User, note: Optional[str] = None) -> list[dict]:
    entry = {
        "status": status,
        "timestamp": datetime.now(timezone.utc).isoformat(),
        "actor_id": actor.id,
        "actor_name": actor.full_name or actor.username,
        "note": note,
    }
    history = list(app.status_history or [])
    history.append(entry)
    return history


# -- Router --

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("/", response_model=ApplicationResponse, status_code=201)
async def apply(data: ApplicationCreate, bg: BackgroundTasks,
                current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.student:
        raise HTTPException(status_code=403, detail="Only students can apply")

    project = await Project.filter(id=data.project_id).prefetch_related("applications").first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status.value != "open":
        raise HTTPException(status_code=400, detail="Project is not open")
    if await Application.filter(project_id=data.project_id, applicant_id=current_user.id).exists():
        raise HTTPException(status_code=400, detail="Already applied")

    active_statuses = (
        ApplicationStatus.accepted, ApplicationStatus.in_progress,
        ApplicationStatus.submitted, ApplicationStatus.approved, ApplicationStatus.completed,
    )
    active_count = await Application.filter(project_id=data.project_id, status__in=active_statuses).count()
    if active_count >= project.max_participants:
        raise HTTPException(status_code=400, detail="Project has reached maximum number of participants")

    application = await Application.create(
        project_id=data.project_id, applicant_id=current_user.id, cover_letter=data.cover_letter,
    )

    application.status_history = _append_history(application, "pending", current_user, None)
    await application.save()

    await log_activity(current_user.id, "apply", f"Applied to project '{project.title}'",
                       "application", application.id)

    owner = await User.filter(id=project.owner_id).first()
    if owner:
        bg.add_task(send_new_application_email, owner.email, owner.username, project.title, current_user.username)

    return application


@router.put("/{app_id}/status", response_model=ApplicationResponse)
async def update_status(app_id: int, data: ApplicationUpdateStatus, bg: BackgroundTasks,
                        current_user: User = Depends(get_current_user)):
    application = await Application.filter(id=app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    project = await Project.filter(id=application.project_id).first()

    is_owner = project.owner_id == current_user.id
    is_applicant = application.applicant_id == current_user.id
    is_admin = current_user.role == RoleEnum.admin

    owner_statuses = {ApplicationStatus.accepted, ApplicationStatus.rejected,
                      ApplicationStatus.approved, ApplicationStatus.revision_requested, ApplicationStatus.completed}
    applicant_statuses = {ApplicationStatus.in_progress, ApplicationStatus.submitted}

    if data.status in owner_statuses and not (is_owner or is_admin):
        raise HTTPException(status_code=403, detail="Only project owner can perform this action")
    if data.status in applicant_statuses and not is_applicant:
        raise HTTPException(status_code=403, detail="Only applicant can perform this action")

    allowed = VALID_TRANSITIONS.get(application.status, [])
    if data.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {application.status.value} to {data.status.value}. "
                   f"Allowed: {[s.value for s in allowed]}"
        )

    application.status = data.status
    if data.status == ApplicationStatus.submitted and data.note:
        application.submission_note = data.note
    if data.status == ApplicationStatus.revision_requested and data.note:
        application.revision_note = data.note
    application.status_history = _append_history(
        application, data.status.value, current_user, data.note
    )
    await application.save()

    await log_activity(current_user.id, "update_application_status",
                       f"Changed status to {data.status.value}", "application", app_id)

    applicant = await User.filter(id=application.applicant_id).first()
    if applicant:
        if data.status in owner_statuses:
            bg.add_task(send_application_status_email, applicant.email, applicant.username,
                        project.title, data.status.value)
        elif data.status == ApplicationStatus.submitted:
            owner = await User.filter(id=project.owner_id).first()
            if owner:
                bg.add_task(send_submission_email, owner.email, owner.username,
                            project.title, applicant.username)

    return application


@router.get("/project/{project_id}", response_model=list[ApplicationResponse])
async def get_project_applications(project_id: int,
                                   page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
                                   current_user: User = Depends(get_current_user)):
    project = await Project.filter(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    skip = (page - 1) * size
    return await Application.filter(project_id=project_id).offset(skip).limit(size)


@router.get("/my", response_model=list[ApplicationResponse])
async def get_my_applications(current_user: User = Depends(get_current_user)):
    return await Application.filter(applicant_id=current_user.id).order_by("-created_at")
