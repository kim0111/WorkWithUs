from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.schemas import UserResponse, UserUpdate
from app.services.services import UserService
from app.api.deps import get_current_user
from app.models.models import User

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    service = UserService(db)
    return await service.get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int,
    data: UserUpdate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserService(db)
    return await service.update_user(user_id, data, current_user)


@router.post("/{user_id}/skills/{skill_id}", status_code=204)
async def add_skill(
    user_id: int,
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserService(db)
    await service.add_skill_to_user(user_id, skill_id, current_user)


@router.delete("/{user_id}/skills/{skill_id}", status_code=204)
async def remove_skill(
    user_id: int,
    skill_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = UserService(db)
    await service.remove_skill_from_user(user_id, skill_id, current_user)
