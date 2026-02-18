from fastapi import APIRouter, Depends, Query
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.schemas import AdminUserUpdate, UserResponse, StatsResponse
from app.services.services import AdminService
from app.api.deps import require_role
from app.models.models import User, RoleEnum

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=StatsResponse)
async def get_stats(
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
):
    service = AdminService(db)
    return await service.get_stats()


@router.get("/users", response_model=list[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0),
    limit: int = Query(20, ge=1, le=100),
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
):
    service = AdminService(db)
    return await service.get_all_users(skip, limit)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: AdminUserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(require_role(RoleEnum.admin)),
):
    service = AdminService(db)
    return await service.update_user(user_id, data)
