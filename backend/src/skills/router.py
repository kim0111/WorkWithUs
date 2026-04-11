from typing import Optional, Sequence
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from src.core.dependencies import get_current_user
from src.core.redis import cache_get, cache_set, cache_delete
from src.skills.models import Skill


# -- Schemas --

class SkillCreate(BaseModel):
    name: str
    category: Optional[str] = None


class SkillResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    class Config:
        from_attributes = True


# -- Router --

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("/", response_model=list[SkillResponse])
async def get_all_skills():
    cached = await cache_get("skills:all")
    if cached:
        return [SkillResponse(id=s["id"], name=s["name"], category=s.get("category")) for s in cached]
    skills = await Skill.all().order_by("name")
    await cache_set("skills:all", [{"id": s.id, "name": s.name, "category": s.category} for s in skills])
    return skills


@router.post("/", response_model=SkillResponse, status_code=201)
async def create_skill(data: SkillCreate, _=Depends(get_current_user)):
    if await Skill.filter(name=data.name).exists():
        raise HTTPException(status_code=400, detail="Skill already exists")
    skill = await Skill.create(name=data.name, category=data.category)
    await cache_delete("skills:all")
    return skill
