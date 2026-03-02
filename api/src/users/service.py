from uuid import UUID

from tortoise.exceptions import DoesNotExist

from src.users.models import CompanyProfile, StudentProfile, User, UserRole
from src.users.schemas import (
    CompanyProfileRead,
    CompanyProfileUpdate,
    StudentProfileRead,
    StudentProfileUpdate,
    UserWithProfileRead,
)


async def _build_student_profile_read(profile: StudentProfile) -> StudentProfileRead:
    await profile.fetch_related("skills")
    return StudentProfileRead(
        first_name=profile.first_name,
        last_name=profile.last_name,
        university=profile.university,
        faculty=profile.faculty,
        year_of_study=profile.year_of_study,
        bio=profile.bio,
        skills=[s.name for s in profile.skills],
    )


async def get_user_with_profile(user: User) -> UserWithProfileRead:
    result = UserWithProfileRead(
        id=user.id,
        email=user.email,
        role=user.role,
        is_active=user.is_active,
    )
    if user.role == UserRole.STUDENT:
        try:
            profile = await StudentProfile.get(user=user)
            result.student_profile = await _build_student_profile_read(profile)
        except DoesNotExist:
            pass
    elif user.role == UserRole.COMPANY:
        try:
            profile = await CompanyProfile.get(user=user)
            result.company_profile = CompanyProfileRead(
                company_name=profile.company_name,
                description=profile.description,
                website=profile.website,
                contact_person=profile.contact_person,
            )
        except DoesNotExist:
            pass
    return result


async def get_user_by_id(user_id: UUID) -> UserWithProfileRead | None:
    user = await User.get_or_none(id=user_id)
    if not user:
        return None
    return await get_user_with_profile(user)


async def update_student_profile(
    user: User, data: StudentProfileUpdate
) -> UserWithProfileRead:
    profile = await StudentProfile.get(user=user)
    update = data.model_dump(exclude_unset=True, exclude={"skill_ids"})
    if update:
        await profile.update_from_dict(update)
        await profile.save()
    if data.skill_ids is not None:
        from src.skills.models import Skill

        skills = await Skill.filter(id__in=data.skill_ids)
        await profile.skills.clear()
        await profile.skills.add(*skills)
    return await get_user_with_profile(user)


async def update_company_profile(
    user: User, data: CompanyProfileUpdate
) -> UserWithProfileRead:
    profile = await CompanyProfile.get(user=user)
    update = data.model_dump(exclude_unset=True)
    if update:
        await profile.update_from_dict(update)
        await profile.save()
    return await get_user_with_profile(user)
