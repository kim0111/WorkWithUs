from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


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
