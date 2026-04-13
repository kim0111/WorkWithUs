from typing import Literal, Optional
from fastapi import APIRouter, Depends, HTTPException, Query
from src.core.dependencies import get_current_user
from src.users.models import User
from src.projects.models import ProjectStatus
from src.projects import service
from src.projects.schemas import (
    ProjectCreate, ProjectUpdate, ProjectResponse, ProjectListResponse,
)

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate, current_user: User = Depends(get_current_user)):
    return await service.create_project(
        current_user, data.title, data.description,
        data.max_participants, data.deadline, data.skill_ids, data.is_student_project,
    )


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    status: Optional[ProjectStatus] = None, owner_id: Optional[int] = None,
    is_student_project: Optional[bool] = None, search: Optional[str] = None,
    skill_ids: Optional[list[int]] = Query(None),
    sort: Literal["newest", "deadline"] = Query("newest"),
):
    return await service.list_projects(
        page, size, status, owner_id, is_student_project, search, skill_ids, sort,
    )


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int):
    return await service.get_project(project_id)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, data: ProjectUpdate,
                         current_user: User = Depends(get_current_user)):
    return await service.update_project(project_id, data.model_dump(exclude_unset=True), current_user)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int, current_user: User = Depends(get_current_user)):
    await service.delete_project(project_id, current_user)
