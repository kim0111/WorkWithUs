from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from tortoise.functions import Avg, Count
from src.core.dependencies import get_current_user
from src.core.email import send_review_email
from src.users.models import User
from src.projects.models import Project
from src.applications.models import Application, ApplicationStatus
from src.reviews.models import Review
from src.notifications.router import create_notification


# -- Schemas --

class ReviewCreate(BaseModel):
    reviewee_id: int
    project_id: int
    application_id: Optional[int] = None
    rating: float = Field(..., ge=1.0, le=5.0)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    reviewer_id: int
    reviewee_id: int
    project_id: int
    application_id: Optional[int] = None
    rating: float
    comment: Optional[str] = None
    review_type: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


class UserRatingResponse(BaseModel):
    user_id: int
    average_rating: float
    total_reviews: int


# -- Router --

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewResponse, status_code=201)
async def create_review(data: ReviewCreate, bg: BackgroundTasks,
                        current_user: User = Depends(get_current_user)):
    if current_user.id == data.reviewee_id:
        raise HTTPException(status_code=400, detail="Cannot review yourself")

    project = await Project.filter(id=data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    is_owner = project.owner_id == current_user.id
    review_type = "owner_to_student" if is_owner else "student_to_owner"

    existing = await Review.filter(
        reviewer_id=current_user.id, project_id=data.project_id, review_type=review_type
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already reviewed this user for this project")

    if data.application_id:
        app = await Application.filter(id=data.application_id).first()
        if not app or app.status not in (ApplicationStatus.approved, ApplicationStatus.completed):
            raise HTTPException(status_code=400, detail="Can only review after work is approved/completed")

    review = await Review.create(
        reviewer_id=current_user.id, reviewee_id=data.reviewee_id,
        project_id=data.project_id, application_id=data.application_id,
        rating=data.rating, comment=data.comment, review_type=review_type,
    )

    reviewee = await User.filter(id=data.reviewee_id).first()
    if reviewee:
        await create_notification(
            data.reviewee_id, "New Review",
            f"{current_user.username} left you a {data.rating}/5 review",
            notification_type="review", link=f"/profile/{data.reviewee_id}"
        )
        bg.add_task(send_review_email, reviewee.email, reviewee.username,
                    current_user.username, data.rating)

    return review


@router.get("/user/{user_id}", response_model=list[ReviewResponse])
async def get_user_reviews(user_id: int, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)):
    skip = (page - 1) * size
    return await Review.filter(reviewee_id=user_id).order_by("-created_at").offset(skip).limit(size)


@router.get("/user/{user_id}/rating", response_model=UserRatingResponse)
async def get_user_rating(user_id: int):
    result = await Review.filter(reviewee_id=user_id).annotate(
        avg_rating=Avg("rating"), total=Count("id")
    ).values("avg_rating", "total")
    if result:
        avg = result[0]["avg_rating"] or 0.0
        total = result[0]["total"] or 0
    else:
        avg, total = 0.0, 0
    return UserRatingResponse(user_id=user_id, average_rating=round(float(avg), 2), total_reviews=int(total))
