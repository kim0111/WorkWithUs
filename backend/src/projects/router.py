from datetime import datetime
from typing import Optional, Sequence
from pydantic import BaseModel, Field
from sqlalchemy import select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import selectinload
from fastapi import APIRouter, Depends, HTTPException, Query
from src.database.postgres import get_db
from src.core.dependencies import get_current_user
from src.core.redis import cache_get, cache_set, cache_delete_pattern
from src.users.models import User, RoleEnum
from src.users.schemas import SkillOut
from src.projects.models import Project, ProjectStatus, ProjectFile
from src.skills.router import SkillRepository


# ── Schemas ──────────────────────────────────────────

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


# ── Repository ───────────────────────────────────────

class ProjectRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_by_id(self, project_id: int) -> Optional[Project]:
        result = await self.db.execute(
            select(Project)
            .options(selectinload(Project.required_skills), selectinload(Project.attachments))
            .where(Project.id == project_id)
        )
        return result.scalar_one_or_none()

    async def get_all(self, skip=0, limit=20, status=None, owner_id=None,
                      is_student_project=None, search=None) -> Sequence[Project]:
        query = select(Project).options(selectinload(Project.required_skills), selectinload(Project.attachments))
        if status:
            query = query.where(Project.status == status)
        if owner_id:
            query = query.where(Project.owner_id == owner_id)
        if is_student_project is not None:
            query = query.where(Project.is_student_project == is_student_project)
        if search:
            query = query.where(Project.title.ilike(f"%{search}%"))
        return (await self.db.execute(query.order_by(Project.created_at.desc()).offset(skip).limit(limit))).scalars().all()

    async def count(self, status=None, owner_id=None, is_student_project=None, search=None) -> int:
        query = select(func.count(Project.id))
        if status:
            query = query.where(Project.status == status)
        if owner_id:
            query = query.where(Project.owner_id == owner_id)
        if is_student_project is not None:
            query = query.where(Project.is_student_project == is_student_project)
        if search:
            query = query.where(Project.title.ilike(f"%{search}%"))
        return (await self.db.execute(query)).scalar()

    async def create(self, project: Project) -> Project:
        self.db.add(project)
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def update(self, project: Project) -> Project:
        await self.db.flush()
        await self.db.refresh(project)
        return project

    async def delete(self, project: Project):
        await self.db.delete(project)


# ── Service ──────────────────────────────────────────

class ProjectService:
    def __init__(self, db: AsyncSession):
        self.repo = ProjectRepository(db)
        self.skill_repo = SkillRepository(db)

    async def create(self, data: ProjectCreate, current_user: User) -> Project:
        if data.is_student_project and current_user.role != RoleEnum.student:
            raise HTTPException(status_code=403, detail="Only students can create student projects")
        if not data.is_student_project and current_user.role not in (RoleEnum.company, RoleEnum.admin):
            raise HTTPException(status_code=403, detail="Only companies can create company projects")

        # Strip timezone info from deadline if it exists (database expects naive datetime)
        deadline = data.deadline
        if deadline and deadline.tzinfo is not None:
            deadline = deadline.replace(tzinfo=None)

        project = Project(
            title=data.title, description=data.description, owner_id=current_user.id,
            max_participants=data.max_participants, deadline=deadline,
            is_student_project=data.is_student_project,
        )
        project = await self.repo.create(project)
        if data.skill_ids:
            skills = await self.skill_repo.get_by_ids(data.skill_ids)
            project.required_skills = list(skills)
        await cache_delete_pattern("projects:*")
        return project

    async def get(self, project_id: int) -> Project:
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        return project

    async def list(self, page=1, size=20, status=None, owner_id=None,
                   is_student_project=None, search=None):
        skip = (page - 1) * size
        items = await self.repo.get_all(skip, size, status, owner_id, is_student_project, search)
        total = await self.repo.count(status, owner_id, is_student_project, search)
        return {"items": items, "total": total, "page": page, "size": size}

    async def update(self, project_id: int, data: ProjectUpdate, current_user: User) -> Project:
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.owner_id != current_user.id and current_user.role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(project, field, value)
        await cache_delete_pattern("projects:*")
        return await self.repo.update(project)

    async def delete(self, project_id: int, current_user: User):
        project = await self.repo.get_by_id(project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")
        if project.owner_id != current_user.id and current_user.role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        await self.repo.delete(project)
        await cache_delete_pattern("projects:*")


# ── Router ───────────────────────────────────────────

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    return await ProjectService(db).create(data, current_user)


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    status: Optional[ProjectStatus] = None, owner_id: Optional[int] = None,
    is_student_project: Optional[bool] = None, search: Optional[str] = None,
    db: AsyncSession = Depends(get_db),
):
    return await ProjectService(db).list(page, size, status, owner_id, is_student_project, search)


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int, db: AsyncSession = Depends(get_db)):
    return await ProjectService(db).get(project_id)


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, data: ProjectUpdate, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    return await ProjectService(db).update(project_id, data, current_user)


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int, db: AsyncSession = Depends(get_db),
                         current_user: User = Depends(get_current_user)):
    await ProjectService(db).delete(project_id, current_user)
