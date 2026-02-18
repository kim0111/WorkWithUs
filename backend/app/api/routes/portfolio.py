from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.schemas import PortfolioItemCreate, PortfolioItemResponse
from app.services.services import PortfolioService
from app.api.deps import get_current_user
from app.models.models import User

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.post("/", response_model=PortfolioItemResponse, status_code=201)
async def add_portfolio_item(
    data: PortfolioItemCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PortfolioService(db)
    return await service.add_item(data, current_user)


@router.get("/user/{user_id}", response_model=list[PortfolioItemResponse])
async def get_portfolio(user_id: int, db: AsyncSession = Depends(get_db)):
    service = PortfolioService(db)
    return await service.get_portfolio(user_id)


@router.delete("/{item_id}", status_code=204)
async def delete_portfolio_item(
    item_id: int,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = PortfolioService(db)
    await service.delete_item(item_id, current_user)
