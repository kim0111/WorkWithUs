from fastapi import APIRouter, Depends

from src.auth.dependencies import require_role
from src.skills.schemas import SkillCreate, SkillRead
from src.skills import service
from src.users.models import UserRole

router = APIRouter()


@router.get("", response_model=list[SkillRead])
async def list_skills():
    return await service.list_skills()


@router.post("", response_model=SkillRead, status_code=201)
async def create_skill(
    body: SkillCreate,
    _=Depends(require_role(UserRole.ADMIN)),
):
    return await service.create_skill(body)
