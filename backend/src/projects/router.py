from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from src.core.dependencies import get_current_user
from src.core.redis import cache_get, cache_set, cache_delete_pattern
from src.users.models import User, RoleEnum
from src.users.schemas import SkillOut
from src.projects.models import Project, ProjectStatus, ProjectFile
from src.skills.models import Skill


# -- Schemas --

class ProjectFileResponse(BaseModel):
    id: int
    filename: str
    object_name: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    file_type: str
    created_at: datetime
    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    max_participants: int = Field(default=1, ge=1)
    deadline: Optional[datetime] = None
    skill_ids: list[int] = []
    is_student_project: bool = False


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    max_participants: Optional[int] = None
    deadline: Optional[datetime] = None


class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str
    owner_id: int
    status: ProjectStatus
    max_participants: int
    deadline: Optional[datetime] = None
    is_student_project: bool
    required_skills: list[SkillOut] = []
    attachments: list[ProjectFileResponse] = []
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    size: int


# -- Helper --

def _build_project_filter(status=None, owner_id=None, is_student_project=None, search=None):
    filters = {}
    if status:
        filters["status"] = status
    if owner_id:
        filters["owner_id"] = owner_id
    if is_student_project is not None:
        filters["is_student_project"] = is_student_project
    q = Project.filter(**filters)
    if search:
        q = q.filter(title__icontains=search)
    return q


# -- Router --

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate, current_user: User = Depends(get_current_user)):
    if data.is_student_project and current_user.role != RoleEnum.student:
        raise HTTPException(status_code=403, detail="Only students can create student projects")
    if not data.is_student_project and current_user.role not in (RoleEnum.company, RoleEnum.admin):
        raise HTTPException(status_code=403, detail="Only companies can create company projects")

    deadline = data.deadline
    if deadline and deadline.tzinfo is not None:
        deadline = deadline.replace(tzinfo=None)

    project = await Project.create(
        title=data.title, description=data.description, owner_id=current_user.id,
        max_participants=data.max_participants, deadline=deadline,
        is_student_project=data.is_student_project,
    )
    if data.skill_ids:
        skills = await Skill.filter(id__in=data.skill_ids)
        await project.required_skills.add(*skills)
    await project.fetch_related("required_skills", "attachments")
    await cache_delete_pattern("projects:*")
    return project


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    status: Optional[ProjectStatus] = None, owner_id: Optional[int] = None,
    is_student_project: Optional[bool] = None, search: Optional[str] = None,
):
    skip = (page - 1) * size
    q = _build_project_filter(status, owner_id, is_student_project, search)
    total = await q.count()
    items = await q.prefetch_related("required_skills", "attachments").order_by("-created_at").offset(skip).limit(size)
    return {"items": items, "total": total, "page": page, "size": size}


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int):
    project = await Project.filter(id=project_id).prefetch_related("required_skills", "attachments").first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, data: ProjectUpdate,
                         current_user: User = Depends(get_current_user)):
    project = await Project.filter(id=project_id).prefetch_related("required_skills", "attachments").first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    await project.update_from_dict(data.model_dump(exclude_unset=True)).save()
    await cache_delete_pattern("projects:*")
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int, current_user: User = Depends(get_current_user)):
    project = await Project.filter(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    await project.delete()
    await cache_delete_pattern("projects:*")
