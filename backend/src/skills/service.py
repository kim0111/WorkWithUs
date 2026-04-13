from fastapi import HTTPException
from src.core.redis import cache_get, cache_set, cache_delete
from src.skills import repository
from src.skills.models import Skill
from src.skills.schemas import SkillResponse

CACHE_KEY = "skills:all"


async def list_skills() -> list[SkillResponse]:
    cached = await cache_get(CACHE_KEY)
    if cached:
        return [SkillResponse(**s) for s in cached]
    skills = await repository.get_all_skills()
    await cache_set(CACHE_KEY, [{"id": s.id, "name": s.name, "category": s.category} for s in skills])
    return skills


async def create_skill(name: str, category: str | None = None) -> Skill:
    if await repository.get_skill_by_name(name):
        raise HTTPException(status_code=400, detail="Skill already exists")
    skill = await repository.create_skill(name, category)
    await cache_delete(CACHE_KEY)
    return skill
