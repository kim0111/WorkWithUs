from fastapi import APIRouter, Depends, BackgroundTasks, Query
from src.core.dependencies import get_current_user
from src.core.email import send_application_status_email, send_new_application_email, send_submission_email
from src.users.models import User
from src.applications.models import ApplicationStatus
from src.applications import service
from src.applications.schemas import (
    ApplicationCreate, ApplicationInviteCreate, ApplicationUpdateStatus, ApplicationResponse,
)

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("/", response_model=ApplicationResponse, status_code=201)
async def apply(data: ApplicationCreate, bg: BackgroundTasks,
                current_user: User = Depends(get_current_user)):
    application, project = await service.apply(current_user, data.project_id, data.cover_letter)

    owner = await User.filter(id=project.owner_id).first()
    if owner:
        bg.add_task(send_new_application_email, owner.email, owner.username,
                    project.title, current_user.username)
    return application


@router.post("/invite", response_model=ApplicationResponse, status_code=201)
async def invite_student(data: ApplicationInviteCreate, bg: BackgroundTasks,
                         current_user: User = Depends(get_current_user)):
    application, project, student = await service.invite_student(
        current_user, data.project_id, data.student_id, data.message,
    )
    # Notification + email fan-out is added in Task 4.
    return application


@router.put("/{app_id}/status", response_model=ApplicationResponse)
async def update_status(app_id: int, data: ApplicationUpdateStatus, bg: BackgroundTasks,
                        current_user: User = Depends(get_current_user)):
    application, project = await service.update_status(
        app_id, data.status, data.note, current_user,
    )

    owner_statuses = {ApplicationStatus.accepted, ApplicationStatus.rejected,
                      ApplicationStatus.approved, ApplicationStatus.revision_requested,
                      ApplicationStatus.completed}

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
    return await service.get_project_applications(project_id, page, size, current_user)


@router.get("/my", response_model=list[ApplicationResponse])
async def get_my_applications(current_user: User = Depends(get_current_user)):
    return await service.get_my_applications(current_user)
