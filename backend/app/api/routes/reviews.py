from fastapi import APIRouter, Depends
from sqlalchemy.ext.asyncio import AsyncSession
from app.database.session import get_db
from app.schemas.schemas import ReviewCreate, ReviewResponse
from app.services.services import ReviewService
from app.api.deps import get_current_user
from app.models.models import User

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewResponse, status_code=201)
async def create_review(
    data: ReviewCreate,
    db: AsyncSession = Depends(get_db),
    current_user: User = Depends(get_current_user),
):
    service = ReviewService(db)
    return await service.create_review(data, current_user)


@router.get("/user/{user_id}", response_model=list[ReviewResponse])
async def get_user_reviews(user_id: int, db: AsyncSession = Depends(get_db)):
    service = ReviewService(db)
    return await service.get_reviews_for_user(user_id)


@router.get("/user/{user_id}/rating")
async def get_user_rating(user_id: int, db: AsyncSession = Depends(get_db)):
    service = ReviewService(db)
    rating = await service.get_average_rating(user_id)
    return {"user_id": user_id, "average_rating": rating or 0.0}
