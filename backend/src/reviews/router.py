from datetime import datetime, timezone
from typing import Optional, Sequence
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, Float, String, Text, ForeignKey, DateTime, select, func
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks
from src.database.postgres import Base, get_db
from src.core.dependencies import get_current_user
from src.core.email import send_review_email
from src.users.models import User
from src.users.repository import UserRepository
from src.notifications.router import create_notification


# ── Model ────────────────────────────────────────────

class Review(Base):
    __tablename__ = "reviews"

    id = Column(Integer, primary_key=True, index=True)
    reviewer_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    reviewee_id = Column(Integer, ForeignKey("users.id", ondelete="CASCADE"))
    project_id = Column(Integer, ForeignKey("projects.id", ondelete="CASCADE"))
    application_id = Column(Integer, ForeignKey("applications.id", ondelete="CASCADE"), nullable=True)
    rating = Column(Float, nullable=False)
    comment = Column(Text)
    review_type = Column(String(50))  # 'owner_to_student' or 'student_to_owner'
    created_at = Column(DateTime, default=lambda: datetime.utcnow())


# ── Schemas ──────────────────────────────────────────

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


# ── Repository ───────────────────────────────────────

class ReviewRepository:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def get_for_user(self, user_id: int) -> Sequence[Review]:
        return (await self.db.execute(
            select(Review).where(Review.reviewee_id == user_id).order_by(Review.created_at.desc())
        )).scalars().all()

    async def get_by_reviewer_and_project(self, reviewer_id: int, project_id: int,
                                            review_type: str) -> Optional[Review]:
        return (await self.db.execute(
            select(Review).where(
                Review.reviewer_id == reviewer_id,
                Review.project_id == project_id,
                Review.review_type == review_type,
            )
        )).scalar_one_or_none()

    async def create(self, review: Review) -> Review:
        self.db.add(review)
        await self.db.flush()
        await self.db.refresh(review)
        return review

    async def get_avg_rating(self, user_id: int) -> tuple[float, int]:
        avg_result = await self.db.execute(
            select(func.avg(Review.rating)).where(Review.reviewee_id == user_id)
        )
        count_result = await self.db.execute(
            select(func.count(Review.id)).where(Review.reviewee_id == user_id)
        )
        avg = avg_result.scalar() or 0.0
        count = count_result.scalar() or 0
        return float(avg), int(count)


# ── Service ──────────────────────────────────────────

class ReviewService:
    def __init__(self, db: AsyncSession):
        self.repo = ReviewRepository(db)
        self.user_repo = UserRepository(db)

    async def create_review(self, data: ReviewCreate, current_user: User, bg: BackgroundTasks) -> Review:
        if current_user.id == data.reviewee_id:
            raise HTTPException(status_code=400, detail="Cannot review yourself")

        # Determine review type
        from src.projects.router import ProjectRepository
        project = await ProjectRepository(self.repo.db).get_by_id(data.project_id)
        if not project:
            raise HTTPException(status_code=404, detail="Project not found")

        is_owner = project.owner_id == current_user.id
        review_type = "owner_to_student" if is_owner else "student_to_owner"

        # Check for duplicate
        existing = await self.repo.get_by_reviewer_and_project(current_user.id, data.project_id, review_type)
        if existing:
            raise HTTPException(status_code=400, detail="You already reviewed this user for this project")

        # Verify the application is completed/approved
        from src.applications.router import ApplicationRepository, ApplicationStatus
        app_repo = ApplicationRepository(self.repo.db)
        if data.application_id:
            app = await app_repo.get_by_id(data.application_id)
            if not app or app.status not in (ApplicationStatus.approved, ApplicationStatus.completed):
                raise HTTPException(status_code=400, detail="Can only review after work is approved/completed")

        review = await self.repo.create(Review(
            reviewer_id=current_user.id, reviewee_id=data.reviewee_id,
            project_id=data.project_id, application_id=data.application_id,
            rating=data.rating, comment=data.comment, review_type=review_type,
        ))

        # Notification + email
        reviewee = await self.user_repo.get_by_id(data.reviewee_id)
        if reviewee:
            await create_notification(
                data.reviewee_id, "New Review",
                f"{current_user.username} left you a {data.rating}/5 review",
                notification_type="review", link=f"/profile/{data.reviewee_id}"
            )
            bg.add_task(send_review_email, reviewee.email, reviewee.username,
                        current_user.username, data.rating)

        return review

    async def get_for_user(self, user_id: int) -> Sequence[Review]:
        return await self.repo.get_for_user(user_id)

    async def get_rating(self, user_id: int) -> UserRatingResponse:
        avg, count = await self.repo.get_avg_rating(user_id)
        return UserRatingResponse(user_id=user_id, average_rating=round(avg, 2), total_reviews=count)


# ── Router ───────────────────────────────────────────

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewResponse, status_code=201)
async def create_review(data: ReviewCreate, bg: BackgroundTasks,
                        db: AsyncSession = Depends(get_db),
                        current_user: User = Depends(get_current_user)):
    return await ReviewService(db).create_review(data, current_user, bg)


@router.get("/user/{user_id}", response_model=list[ReviewResponse])
async def get_user_reviews(user_id: int, db: AsyncSession = Depends(get_db)):
    return await ReviewService(db).get_for_user(user_id)


@router.get("/user/{user_id}/rating", response_model=UserRatingResponse)
async def get_user_rating(user_id: int, db: AsyncSession = Depends(get_db)):
    return await ReviewService(db).get_rating(user_id)
