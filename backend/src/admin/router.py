from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.postgres import get_db
from src.database.mongodb import get_mongodb
from src.core.dependencies import require_role
from src.core.redis import cache_get, cache_set
from src.users.models import User, RoleEnum
from src.users.schemas import UserResponse
from src.users.repository import UserRepository
from src.projects.router import ProjectRepository
from src.projects.models import ProjectStatus
from src.applications.router import ApplicationRepository


# ── Schemas ──────────────────────────────────────────

class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None
    role: Optional[RoleEnum] = None


class StatsResponse(BaseModel):
    total_users: int
    total_students: int
    total_companies: int
    total_projects: int
    total_applications: int
    active_projects: int
    total_chat_messages: int = 0
    total_notifications: int = 0


# ── Router ───────────────────────────────────────────

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
):
    # Try cache
    cached = await cache_get("admin:stats")
    if cached:
        return StatsResponse(**cached)

    user_repo = UserRepository(db)
    project_repo = ProjectRepository(db)
    app_repo = ApplicationRepository(db)

    # MongoDB counts
    mongo = await get_mongodb()
    chat_count = await mongo.chat_messages.count_documents({})
    notif_count = await mongo.notifications.count_documents({})

    stats = StatsResponse(
        total_users=await user_repo.count(),
        total_students=await user_repo.count_by_role(RoleEnum.student),
        total_companies=await user_repo.count_by_role(RoleEnum.company),
        total_projects=await project_repo.count(),
        total_applications=await app_repo.count(),
        active_projects=await project_repo.count(status=ProjectStatus.open),
        total_chat_messages=chat_count,
        total_notifications=notif_count,
    )
    await cache_set("admin:stats", stats.model_dump(), ttl=60)
    return stats


@router.get("/users", response_model=list[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
):
    return await UserRepository(db).get_all(skip, limit)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, data: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
):
    repo = UserRepository(db)
    user = await repo.get_by_id(user_id)
    if not user:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="User not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(user, field, value)
    return await repo.update(user)
