from uuid import UUID

from fastapi import APIRouter, Depends

from src.applications import service
from src.applications.schemas import ApplicationCreate, ApplicationRead, ApplicationStatusUpdate
from src.auth.dependencies import get_current_user, require_role
from src.users.models import User, UserRole

router = APIRouter()


@router.post(
    "/projects/{project_id}/applications",
    response_model=ApplicationRead,
    status_code=201,
)
async def create_application(
    project_id: UUID,
    body: ApplicationCreate,
    user: User = Depends(require_role(UserRole.STUDENT)),
):
    return await service.create_application(project_id, body, user)


@router.get(
    "/projects/{project_id}/applications",
    response_model=list[ApplicationRead],
)
async def list_project_applications(
    project_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
):
    return await service.list_project_applications(project_id, user)


@router.get("/applications/my", response_model=list[ApplicationRead])
async def my_applications(
    user: User = Depends(require_role(UserRole.STUDENT)),
):
    return await service.list_my_applications(user)


@router.get("/applications/{application_id}", response_model=ApplicationRead)
async def get_application(
    application_id: UUID,
    user: User = Depends(get_current_user),
):
    return await service.get_application(application_id, user)


@router.patch(
    "/applications/{application_id}/status",
    response_model=ApplicationRead,
)
async def update_application_status(
    application_id: UUID,
    body: ApplicationStatusUpdate,
    user: User = Depends(require_role(UserRole.COMPANY)),
):
    return await service.update_application_status(application_id, body, user)
