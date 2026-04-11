from fastapi import APIRouter, Depends, HTTPException
from src.core.dependencies import get_current_user
from src.users.models import User, CompanyProfile, StudentProfile, RoleEnum
from src.users.schemas import (
    UserResponse, UserUpdate,
    CompanyProfileCreate, CompanyProfileResponse,
    StudentProfileCreate, StudentProfileResponse,
)
from src.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


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
    profile = await CompanyProfile.filter(user_id=user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    return profile


@router.put("/{user_id}/company-profile", response_model=CompanyProfileResponse)
async def update_company_profile(user_id: int, data: CompanyProfileCreate,
                                 current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    profile = await CompanyProfile.filter(user_id=user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    await profile.update_from_dict(data.model_dump(exclude_unset=True)).save()
    return profile


# -- Student Profile --

@router.get("/{user_id}/student-profile", response_model=StudentProfileResponse)
async def get_student_profile(user_id: int):
    profile = await StudentProfile.filter(user_id=user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile


@router.put("/{user_id}/student-profile", response_model=StudentProfileResponse)
async def update_student_profile(user_id: int, data: StudentProfileCreate,
                                 current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    profile = await StudentProfile.filter(user_id=user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    await profile.update_from_dict(data.model_dump(exclude_unset=True)).save()
    return profile
