from fastapi import APIRouter, Depends, Query
from src.core.dependencies import require_role
from src.users.models import User, RoleEnum
from src.users.schemas import UserResponse
from src.admin import service
from src.admin.schemas import AdminUserUpdate, StatsResponse

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=StatsResponse)
async def get_stats(current_user: User = Depends(require_role(RoleEnum.admin))):
    return await service.get_stats()


@router.get("/users", response_model=list[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role(RoleEnum.admin)),
):
    return await service.get_all_users(skip, limit)


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, data: AdminUserUpdate,
    current_user: User = Depends(require_role(RoleEnum.admin)),
):
    return await service.update_user(user_id, data.model_dump(exclude_unset=True))
