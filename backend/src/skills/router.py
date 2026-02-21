from typing import Optional, Sequence
from pydantic import BaseModel
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession
from fastapi import APIRouter, Depends, HTTPException
from src.database.postgres import get_db
from src.core.dependencies import get_current_user
from src.core.redis import cache_get, cache_set, cache_delete
from src.skills.models import Skill


# ── Schemas ──────────────────────────────────────────

class SkillCreate(BaseModel):
    name: str
    category: Optional[str] = None


class SkillResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    class Config:
        from_attributes = True


# ── Repository ───────────────────────────────────────

class SkillRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_all(self) -> Sequence[Skill]:
        result = await self.db.execute(select(Skill).order_by(Skill.name))
        return result.scalars().all()

    async def get_by_name(self, name: str) -> Optional[Skill]:
        result = await self.db.execute(select(Skill).where(Skill.name == name))
        return result.scalar_one_or_none()

    async def get_by_ids(self, ids: list[int]) -> Sequence[Skill]:
        result = await self.db.execute(select(Skill).where(Skill.id.in_(ids)))
        return result.scalars().all()

    async def create(self, skill: Skill) -> Skill:
        self.db.add(skill)
        await self.db.flush()
        await self.db.refresh(skill)
        return skill


# ── Service ──────────────────────────────────────────

class SkillService:
    def __init__(self, db: AsyncSession):
        self.repo = SkillRepository(db)

    async def get_all(self) -> Sequence[Skill]:
        cached = await cache_get("skills:all")
        if cached:
            return [Skill(id=s["id"], name=s["name"], category=s.get("category")) for s in cached]
        skills = await self.repo.get_all()
        await cache_set("skills:all", [{"id": s.id, "name": s.name, "category": s.category} for s in skills])
        return skills

    async def create(self, data: SkillCreate) -> Skill:
        if await self.repo.get_by_name(data.name):
            raise HTTPException(status_code=400, detail="Skill already exists")
        skill = await self.repo.create(Skill(name=data.name, category=data.category))
        await cache_delete("skills:all")
        return skill


# ── Router ───────────────────────────────────────────

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("/", response_model=list[SkillResponse])
async def get_all_skills(db: AsyncSession = Depends(get_db)):
    return await SkillService(db).get_all()


@router.post("/", response_model=SkillResponse, status_code=201)
async def create_skill(data: SkillCreate, db: AsyncSession = Depends(get_db),
                       _=Depends(get_current_user)):
    return await SkillService(db).create(data)
