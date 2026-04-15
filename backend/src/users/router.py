from typing import Optional
from fastapi import APIRouter, Depends, Query, HTTPException
from src.core.dependencies import get_current_user
from src.users.models import User, RoleEnum
from src.users.schemas import (
    UserResponse, UserUpdate,
    CompanyProfileCreate, CompanyProfileResponse,
    StudentProfileCreate, StudentProfileResponse,
    StudentSearchResponse,
)
from src.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/search", response_model=StudentSearchResponse)
async def search_students(
    skills: list[int] = Query(default=[]),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    available: bool = Query(False),
    q: Optional[str] = Query(None, min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (RoleEnum.company, RoleEnum.admin):
        raise HTTPException(status_code=403, detail="Only companies can search students")
    return await UserService().search_students(
        skill_ids=skills or None,
        min_rating=min_rating,
        available=available,
        q=q,
        page=page,
        size=size,
    )


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    return await UserService().get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, data: UserUpdate,
                      current_user: User = Depends(get_current_user)):
    return await UserService().update_user(user_id, data, current_user)


@router.post("/{user_id}/skills/{skill_id}", status_code=204)
async def add_skill(user_id: int, skill_id: int,
                    current_user: User = Depends(get_current_user)):
    await UserService().add_skill(user_id, skill_id, current_user)


@router.delete("/{user_id}/skills/{skill_id}", status_code=204)
async def remove_skill(user_id: int, skill_id: int,
                       current_user: User = Depends(get_current_user)):
    await UserService().remove_skill(user_id, skill_id, current_user)


# -- Company Profile --

@router.get("/{user_id}/company-profile", response_model=CompanyProfileResponse)
async def get_company_profile(user_id: int):
    return await UserService().get_company_profile(user_id)


@router.put("/{user_id}/company-profile", response_model=CompanyProfileResponse)
async def update_company_profile(user_id: int, data: CompanyProfileCreate,
                                 current_user: User = Depends(get_current_user)):
    return await UserService().update_company_profile(user_id, data.model_dump(exclude_unset=True), current_user)


# -- Student Profile --

@router.get("/{user_id}/student-profile", response_model=StudentProfileResponse)
async def get_student_profile(user_id: int):
    return await UserService().get_student_profile(user_id)


@router.put("/{user_id}/student-profile", response_model=StudentProfileResponse)
async def update_student_profile(user_id: int, data: StudentProfileCreate,
                                 current_user: User = Depends(get_current_user)):
    return await UserService().update_student_profile(user_id, data.model_dump(exclude_unset=True), current_user)
