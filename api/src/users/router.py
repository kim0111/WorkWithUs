from uuid import UUID

from fastapi import APIRouter, Body, Depends, HTTPException

from src.auth.dependencies import get_current_user
from src.users.models import User, UserRole
from src.users.schemas import (
    CompanyProfileUpdate,
    StudentProfileUpdate,
    UserWithProfileRead,
)
from src.users import service

router = APIRouter()


@router.get("/me", response_model=UserWithProfileRead)
async def get_me(user: User = Depends(get_current_user)):
    return await service.get_user_with_profile(user)


@router.patch("/me/student", response_model=UserWithProfileRead)
async def update_student(
    body: StudentProfileUpdate,
    user: User = Depends(get_current_user),
):
    if user.role != UserRole.STUDENT:
        raise HTTPException(status_code=400, detail="Not a student account")
    return await service.update_student_profile(user, body)


@router.patch("/me/company", response_model=UserWithProfileRead)
async def update_company(
    body: CompanyProfileUpdate,
    user: User = Depends(get_current_user),
):
    if user.role != UserRole.COMPANY:
        raise HTTPException(status_code=400, detail="Not a company account")
    return await service.update_company_profile(user, body)


@router.get("/{user_id}", response_model=UserWithProfileRead)
async def get_user(user_id: UUID, _: User = Depends(get_current_user)):
    result = await service.get_user_by_id(user_id)
    if not result:
        raise HTTPException(status_code=404, detail="User not found")
    return result
