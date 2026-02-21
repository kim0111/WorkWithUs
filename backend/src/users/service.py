from typing import Sequence
from fastapi import HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.users.models import User, RoleEnum
from src.users.schemas import UserUpdate
from src.users.repository import UserRepository
from src.core.redis import cache_get, cache_set, cache_delete


class UserService:
    def __init__(self, db: AsyncSession):
        self.repo = UserRepository(db)

    async def get_user(self, user_id: int) -> User:
        # Try cache first
        cached = await cache_get(f"user:{user_id}")
        if cached:
            user = await self.repo.get_by_id(user_id)
            if user:
                return user

        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        return user

    async def update_user(self, user_id: int, data: UserUpdate, current_user: User) -> User:
        if current_user.id != user_id and current_user.role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        user = await self.repo.get_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        for field, value in data.model_dump(exclude_unset=True).items():
            setattr(user, field, value)
        user = await self.repo.update(user)
        await cache_delete(f"user:{user_id}")
        return user

    async def add_skill(self, user_id: int, skill_id: int, current_user: User):
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        await self.repo.add_skill(user_id, skill_id)
        await cache_delete(f"user:{user_id}")

    async def remove_skill(self, user_id: int, skill_id: int, current_user: User):
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        await self.repo.remove_skill(user_id, skill_id)
        await cache_delete(f"user:{user_id}")

    async def get_all(self, skip: int = 0, limit: int = 20) -> Sequence[User]:
        return await self.repo.get_all(skip, limit)
