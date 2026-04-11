from typing import Sequence
from fastapi import HTTPException
from src.users.models import User, CompanyProfile, StudentProfile, RoleEnum
from src.users.schemas import UserUpdate
from src.core.redis import cache_get, cache_set, cache_delete


class UserService:
    async def get_user(self, user_id: int) -> User:
        cached = await cache_get(f"user:{user_id}")
        if cached:
            return cached

        user = await User.filter(id=user_id).prefetch_related("skills").first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await cache_set(f"user:{user_id}", {
            "id": user.id, "email": user.email, "username": user.username,
            "full_name": user.full_name, "role": user.role.value,
            "avatar_url": user.avatar_url, "bio": user.bio,
            "is_active": user.is_active, "is_blocked": user.is_blocked,
        })
        return user

    async def update_user(self, user_id: int, data: UserUpdate, current_user: User) -> User:
        if current_user.id != user_id and current_user.role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        user = await User.filter(id=user_id).prefetch_related("skills").first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        update_data = data.model_dump(exclude_unset=True)
        await user.update_from_dict(update_data).save()
        await cache_delete(f"user:{user_id}")
        return user

    async def add_skill(self, user_id: int, skill_id: int, current_user: User):
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        from src.skills.models import Skill
        user = await User.filter(id=user_id).first()
        skill = await Skill.filter(id=skill_id).first()
        if not user or not skill:
            raise HTTPException(status_code=404, detail="User or skill not found")
        await user.skills.add(skill)
        await cache_delete(f"user:{user_id}")

    async def remove_skill(self, user_id: int, skill_id: int, current_user: User):
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        from src.skills.models import Skill
        user = await User.filter(id=user_id).first()
        skill = await Skill.filter(id=skill_id).first()
        if not user or not skill:
            raise HTTPException(status_code=404, detail="User or skill not found")
        await user.skills.remove(skill)
        await cache_delete(f"user:{user_id}")

    async def get_all(self, skip: int = 0, limit: int = 20) -> Sequence[User]:
        return await User.all().offset(skip).limit(limit)
