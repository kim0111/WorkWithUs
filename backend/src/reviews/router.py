from fastapi import APIRouter, Depends, BackgroundTasks, Query
from src.core.dependencies import get_current_user
from src.core.email import send_review_email
from src.users.models import User
from src.reviews import service
from src.reviews.schemas import ReviewCreate, ReviewResponse, UserRatingResponse

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewResponse, status_code=201)
async def create_review(data: ReviewCreate, bg: BackgroundTasks,
                        current_user: User = Depends(get_current_user)):
    review, reviewee = await service.create_review(
        current_user, data.reviewee_id, data.project_id,
        data.application_id, data.rating, data.comment,
    )
    if reviewee:
        bg.add_task(send_review_email, reviewee.email, reviewee.username,
                    current_user.username, data.rating)
    return review


@router.get("/user/{user_id}", response_model=list[ReviewResponse])
async def get_user_reviews(user_id: int, page: int = Query(1, ge=1),
                           size: int = Query(20, ge=1, le=100)):
    return await service.get_user_reviews(user_id, page, size)


@router.get("/user/{user_id}/rating", response_model=UserRatingResponse)
async def get_user_rating(user_id: int):
    return await service.get_user_rating(user_id)
