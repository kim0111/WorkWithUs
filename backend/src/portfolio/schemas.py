from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field


class PortfolioItemCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    project_url: Optional[str] = None
    image_url: Optional[str] = None


class PortfolioItemResponse(BaseModel):
    id: int
    student_id: int
    title: str
    description: Optional[str] = None
    project_url: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime

    class Config:
        from_attributes = True
