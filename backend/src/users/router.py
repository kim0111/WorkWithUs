from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.postgres import get_db
from src.core.dependencies import get_current_user
from src.users.models import User
from src.users.schemas import UserResponse, UserUpdate
from src.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await UserService(db).get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, data: UserUpdate, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    return await UserService(db).update_user(user_id, data, current_user)


@router.post("/{user_id}/skills/{skill_id}", status_code=204)
async def add_skill(user_id: int, skill_id: int, db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    await UserService(db).add_skill(user_id, skill_id, current_user)


@router.delete("/{user_id}/skills/{skill_id}", status_code=204)
async def remove_skill(user_id: int, skill_id: int, db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    await UserService(db).remove_skill(user_id, skill_id, current_user)
