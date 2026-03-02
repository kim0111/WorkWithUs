from uuid import UUID

from fastapi import APIRouter, Depends, Query

from src.auth.dependencies import get_current_user, require_role
from src.projects import service
from src.projects.models import ProjectStatus
from src.projects.schemas import ProjectCreate, ProjectListRead, ProjectRead, ProjectUpdate
from src.users.models import User, UserRole

router = APIRouter()


@router.post("", response_model=ProjectRead, status_code=201)
async def create_project(
    body: ProjectCreate,
    user: User = Depends(require_role(UserRole.COMPANY)),
):
    return await service.create_project(body, user)


@router.get("", response_model=list[ProjectListRead])
async def list_projects(
    status: ProjectStatus | None = Query(None),
    skill: int | None = Query(None),
    search: str | None = Query(None),
    _: User = Depends(get_current_user),
):
    return await service.list_projects(status_filter=status, skill_id=skill, search=search)


@router.get("/my", response_model=list[ProjectListRead])
async def my_projects(
    user: User = Depends(require_role(UserRole.COMPANY)),
):
    return await service.list_my_projects(user)


@router.get("/{project_id}", response_model=ProjectRead)
async def get_project(
    project_id: UUID,
    _: User = Depends(get_current_user),
):
    return await service.get_project(project_id)


@router.patch("/{project_id}", response_model=ProjectRead)
async def update_project(
    project_id: UUID,
    body: ProjectUpdate,
    user: User = Depends(require_role(UserRole.COMPANY)),
):
    return await service.update_project(project_id, body, user)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: UUID,
    user: User = Depends(require_role(UserRole.COMPANY)),
):
    await service.delete_project(project_id, user)
