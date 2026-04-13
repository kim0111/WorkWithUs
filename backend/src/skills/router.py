from fastapi import APIRouter, Depends
from src.core.dependencies import get_current_user
from src.skills import service
from src.skills.schemas import SkillCreate, SkillResponse

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("/", response_model=list[SkillResponse])
async def get_all_skills():
    return await service.list_skills()


@router.post("/", response_model=SkillResponse, status_code=201)
async def create_skill(data: SkillCreate, _=Depends(get_current_user)):
    return await service.create_skill(data.name, data.category)
