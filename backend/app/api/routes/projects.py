from typing import Optional
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.schemas import ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse
from app.services.services import ProjectService
from app.api.deps import get_current_user
from app.models.models import User, ProjectStatus

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(
    data: ProjectCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    return await service.create_project(data, current_user)


@router.get("/", response_model=ProjectListResponse)
async def get_projects(
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    status: Optional[ProjectStatus] = None,
    owner_id: Optional[int] = None,
    is_student_project: Optional[bool] = None,
    search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    service = ProjectService(db)
    return await service.get_projects(page, size, status, owner_id, is_student_project, search)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    service = ProjectService(db)
    return await service.get_project(project_id)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(
    project_id: int,
    data: ProjectUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    return await service.update_project(project_id, data, current_user)


@router.delete("/{project_id}", status_code=204)
async def delete_project(
    project_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ProjectService(db)
    await service.delete_project(project_id, current_user)
