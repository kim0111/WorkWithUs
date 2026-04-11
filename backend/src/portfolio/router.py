from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from src.core.dependencies import get_current_user
from src.users.models import User, StudentProfile, RoleEnum
from src.portfolio.models import PortfolioItem


# -- Schemas --

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


# -- Router --

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.post("/", response_model=PortfolioItemResponse, status_code=201)
async def add_item(data: PortfolioItemCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.student:
        raise HTTPException(status_code=403, detail="Only students have portfolios")
    student = await StudentProfile.filter(user_id=current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    item = await PortfolioItem.create(
        student_id=student.id, title=data.title, description=data.description,
        project_url=data.project_url, image_url=data.image_url,
    )
    return item


@router.get("/user/{user_id}", response_model=list[PortfolioItemResponse])
async def get_portfolio(user_id: int):
    student = await StudentProfile.filter(user_id=user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return await PortfolioItem.filter(student_id=student.id).order_by("-created_at")


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int, current_user: User = Depends(get_current_user)):
    item = await PortfolioItem.filter(id=item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    student = await StudentProfile.filter(user_id=current_user.id).first()
    if not student or item.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    await item.delete()
