from fastapi import APIRouter, Depends
from src.core.dependencies import get_current_user
from src.users.models import User
from src.portfolio import service
from src.portfolio.schemas import PortfolioItemCreate, PortfolioItemResponse

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.post("/", response_model=PortfolioItemResponse, status_code=201)
async def add_item(data: PortfolioItemCreate, current_user: User = Depends(get_current_user)):
    return await service.add_item(
        current_user, data.title, data.description, data.project_url, data.image_url,
    )


@router.get("/user/{user_id}", response_model=list[PortfolioItemResponse])
async def get_portfolio(user_id: int):
    return await service.get_portfolio(user_id)


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int, current_user: User = Depends(get_current_user)):
    await service.delete_item(item_id, current_user)
