from fastapi import HTTPException
from src.core.redis import cache_get, cache_set
from src.admin import repository
from src.admin.schemas import StatsResponse
from src.users.models import User
from src.users.schemas import UserResponse


async def get_stats() -> StatsResponse:
    cached = await cache_get("admin:stats")
    if cached:
        return StatsResponse(**cached)

    stats = StatsResponse(
        total_users=await repository.count_users(),
        total_students=await repository.count_students(),
        total_companies=await repository.count_companies(),
        total_projects=await repository.count_projects(),
        total_applications=await repository.count_applications(),
        active_projects=await repository.count_active_projects(),
        total_chat_messages=await repository.count_chat_messages(),
        total_notifications=await repository.count_notifications(),
    )
    await cache_set("admin:stats", stats.model_dump(), ttl=60)
    return stats


async def get_all_users(skip: int, limit: int) -> list[User]:
    return await repository.get_all_users(skip, limit)


async def update_user(user_id: int, data: dict) -> User:
    user = await repository.get_user_by_id(user_id)
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    return await repository.update_user(user, data)
