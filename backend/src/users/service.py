from fastapi import HTTPException
from src.users import repository
from src.users.models import User, CompanyProfile, StudentProfile, RoleEnum
from src.users.schemas import UserUpdate
from src.core.redis import cache_get, cache_set, cache_delete


class UserService:
    async def get_user(self, user_id: int) -> User:
        cached = await cache_get(f"user:{user_id}")
        if cached:
            return cached

        user = await repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await cache_set(f"user:{user_id}", {
            "id": user.id, "email": user.email, "username": user.username,
            "full_name": user.full_name, "role": user.role.value,
            "avatar_url": user.avatar_url, "bio": user.bio,
            "is_active": user.is_active, "is_blocked": user.is_blocked,
            "created_at": user.created_at.isoformat(),
            "skills": [{"id": s.id, "name": s.name, "category": s.category} for s in user.skills],
        })
        return user

    async def update_user(self, user_id: int, data: UserUpdate, current_user: User) -> User:
        if current_user.id != user_id and current_user.role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        user = await repository.get_user_by_id(user_id)
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await repository.update_user(user, data.model_dump(exclude_unset=True))
        await cache_delete(f"user:{user_id}")
        return user

    async def add_skill(self, user_id: int, skill_id: int, current_user: User):
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        user = await repository.get_user_by_id_bare(user_id)
        skill = await repository.get_skill_by_id(skill_id)
        if not user or not skill:
            raise HTTPException(status_code=404, detail="User or skill not found")
        await repository.add_skill(user, skill)
        await cache_delete(f"user:{user_id}")

    async def remove_skill(self, user_id: int, skill_id: int, current_user: User):
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        user = await repository.get_user_by_id_bare(user_id)
        skill = await repository.get_skill_by_id(skill_id)
        if not user or not skill:
            raise HTTPException(status_code=404, detail="User or skill not found")
        await repository.remove_skill(user, skill)
        await cache_delete(f"user:{user_id}")

    async def get_company_profile(self, user_id: int) -> CompanyProfile:
        profile = await repository.get_company_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Company profile not found")
        return profile

    async def update_company_profile(self, user_id: int, data: dict, current_user: User) -> CompanyProfile:
        if current_user.id != user_id and current_user.role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        profile = await repository.get_company_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Company profile not found")
        return await repository.update_company_profile(profile, data)

    async def get_student_profile(self, user_id: int) -> StudentProfile:
        profile = await repository.get_student_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Student profile not found")
        return profile

    async def update_student_profile(self, user_id: int, data: dict, current_user: User) -> StudentProfile:
        if current_user.id != user_id and current_user.role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        profile = await repository.get_student_profile(user_id)
        if not profile:
            raise HTTPException(status_code=404, detail="Student profile not found")
        return await repository.update_student_profile(profile, data)
