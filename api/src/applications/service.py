from uuid import UUID

from fastapi import HTTPException, status
from tortoise.exceptions import IntegrityError

from src.applications.models import Application, ApplicationStatus
from src.applications.schemas import ApplicationCreate, ApplicationRead, ApplicationStatusUpdate
from src.projects.models import Project, ProjectStatus
from src.users.models import User


def _app_to_read(app: Application) -> ApplicationRead:
    return ApplicationRead(
        id=app.id,
        project_id=app.project_id,
        student_id=app.student_id,
        cover_letter=app.cover_letter,
        status=app.status,
        created_at=app.created_at,
        updated_at=app.updated_at,
    )


async def create_application(project_id: UUID, data: ApplicationCreate, student: User) -> ApplicationRead:
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.status != ProjectStatus.PUBLISHED:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only apply to published projects",
        )
    try:
        app = await Application.create(
            project=project,
            student=student,
            cover_letter=data.cover_letter,
        )
    except IntegrityError:
        raise HTTPException(
            status_code=status.HTTP_409_CONFLICT,
            detail="You have already applied to this project",
        )
    return _app_to_read(app)


async def list_project_applications(project_id: UUID, company: User) -> list[ApplicationRead]:
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the project owner")
    apps = await Application.filter(project_id=project_id).order_by("-created_at")
    return [_app_to_read(a) for a in apps]


async def list_my_applications(student: User) -> list[ApplicationRead]:
    apps = await Application.filter(student=student).order_by("-created_at")
    return [_app_to_read(a) for a in apps]


async def get_application(application_id: UUID, user: User) -> ApplicationRead:
    app = await Application.get_or_none(id=application_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    project = await Project.get(id=app.project_id)
    if app.student_id != user.id and project.company_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")
    return _app_to_read(app)


async def update_application_status(
    application_id: UUID, data: ApplicationStatusUpdate, company: User
) -> ApplicationRead:
    app = await Application.get_or_none(id=application_id)
    if not app:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    project = await Project.get(id=app.project_id)
    if project.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the project owner")
    if app.status != ApplicationStatus.PENDING:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Can only change status of pending applications",
        )
    app.status = data.status
    await app.save()
    return _app_to_read(app)
