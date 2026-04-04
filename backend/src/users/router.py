from fastapi import APIRouter, Depends, HTTPException
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.postgres import get_db
from src.core.dependencies import get_current_user
from src.users.models import User, RoleEnum
from src.users.schemas import (
    UserResponse, UserUpdate,
    CompanyProfileCreate, CompanyProfileResponse,
    StudentProfileCreate, StudentProfileResponse,
)
from src.users.service import UserService
from src.users.repository import CompanyProfileRepository, StudentProfileRepository

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int, db: AsyncSession = Depends(get_db)):
    return await UserService(db).get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, data: UserUpdate, db: AsyncSession = Depends(get_db),
                      current_user: User = Depends(get_current_user)):
    return await UserService(db).update_user(user_id, data, current_user)


@router.post("/{user_id}/skills/{skill_id}", status_code=204)
async def add_skill(user_id: int, skill_id: int, db: AsyncSession = Depends(get_db),
                    current_user: User = Depends(get_current_user)):
    await UserService(db).add_skill(user_id, skill_id, current_user)


@router.delete("/{user_id}/skills/{skill_id}", status_code=204)
async def remove_skill(user_id: int, skill_id: int, db: AsyncSession = Depends(get_db),
                       current_user: User = Depends(get_current_user)):
    await UserService(db).remove_skill(user_id, skill_id, current_user)


# ── Company Profile ─────────────────────────────────

@router.get("/{user_id}/company-profile", response_model=CompanyProfileResponse)
async def get_company_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    profile = await CompanyProfileRepository(db).get_by_user_id(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    return profile


@router.put("/{user_id}/company-profile", response_model=CompanyProfileResponse)
async def update_company_profile(user_id: int, data: CompanyProfileCreate,
                                 db: AsyncSession = Depends(get_db),
                                 current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    repo = CompanyProfileRepository(db)
    profile = await repo.get_by_user_id(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    return await repo.update(profile)


# ── Student Profile ─────────────────────────────────

@router.get("/{user_id}/student-profile", response_model=StudentProfileResponse)
async def get_student_profile(user_id: int, db: AsyncSession = Depends(get_db)):
    profile = await StudentProfileRepository(db).get_by_user_id(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile


@router.put("/{user_id}/student-profile", response_model=StudentProfileResponse)
async def update_student_profile(user_id: int, data: StudentProfileCreate,
                                 db: AsyncSession = Depends(get_db),
                                 current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    repo = StudentProfileRepository(db)
    profile = await repo.get_by_user_id(user_id)
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    for field, value in data.model_dump(exclude_unset=True).items():
        setattr(profile, field, value)
    return await repo.update(profile)
