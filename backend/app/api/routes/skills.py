from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.schemas import SkillCreate, SkillResponse
from app.services.services import SkillService
from app.api.deps import get_current_user
from app.models.models import User

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.post("/", response_model=SkillResponse, status_code=201)
async def create_skill(
    data: SkillCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = SkillService(db)
    return await service.create_skill(data)


@router.get("/", response_model=list[SkillResponse])
async def get_all_skills(db: AsyncSession = Depends(get_db)):
    service = SkillService(db)
    return await service.get_all_skills()
