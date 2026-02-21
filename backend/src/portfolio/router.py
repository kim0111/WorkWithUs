from datetime import datetime, timezone
from typing import Optional, Sequence
from pydantic import BaseModel, Field
from sqlalchemy import Column, Integer, String, Text, ForeignKey, DateTime, select
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy.orm import relationship
from fastapi import APIRouter, Depends, HTTPException
from src.database.postgres import Base, get_db
from src.core.dependencies import get_current_user
from src.users.models import User, RoleEnum
from src.users.repository import StudentProfileRepository


# ── Model ────────────────────────────────────────────

class PortfolioItem(Base):
    __tablename__ = "portfolio_items"

    id = Column(Integer, primary_key=True, index=True)
    student_id = Column(Integer, ForeignKey("student_profiles.id", ondelete="CASCADE"))
    title = Column(String(255), nullable=False)
    description = Column(Text)
    project_url = Column(String(500))
    image_url = Column(String(500))
    created_at = Column(DateTime, default=lambda: datetime.utcnow())

    student = relationship("StudentProfile", back_populates="portfolio_items")


# ── Schemas ──────────────────────────────────────────

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


# ── Router ───────────────────────────────────────────

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.post("/", response_model=PortfolioItemResponse, status_code=201)
async def add_item(data: PortfolioItemCreate, db: AsyncSession = Depends(get_db),
                   current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.student:
        raise HTTPException(status_code=403, detail="Only students have portfolios")
    student = await StudentProfileRepository(db).get_by_user_id(current_user.id)
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    item = PortfolioItem(student_id=student.id, title=data.title, description=data.description,
                         project_url=data.project_url, image_url=data.image_url)
    db.add(item)
    await db.flush()
    await db.refresh(item)
    return item


@router.get("/user/{user_id}", response_model=list[PortfolioItemResponse])
async def get_portfolio(user_id: int, db: AsyncSession = Depends(get_db)):
    student = await StudentProfileRepository(db).get_by_user_id(user_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    result = await db.execute(
        select(PortfolioItem).where(PortfolioItem.student_id == student.id).order_by(PortfolioItem.created_at.desc())
    )
    return result.scalars().all()


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    result = await db.execute(select(PortfolioItem).where(PortfolioItem.id == item_id))
    item = result.scalar_one_or_none()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    student = await StudentProfileRepository(db).get_by_user_id(current_user.id)
    if not student or item.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    await db.delete(item)
