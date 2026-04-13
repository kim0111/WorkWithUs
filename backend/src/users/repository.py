from src.users.models import User, CompanyProfile, StudentProfile
from src.skills.models import Skill


async def get_user_by_id(user_id: int) -> User | None:
    return await User.filter(id=user_id).prefetch_related("skills").first()


async def get_user_by_id_bare(user_id: int) -> User | None:
    return await User.filter(id=user_id).first()


async def update_user(user: User, data: dict) -> User:
    await user.update_from_dict(data).save()
    return user


async def get_skill_by_id(skill_id: int) -> Skill | None:
    return await Skill.filter(id=skill_id).first()


async def add_skill(user: User, skill: Skill) -> None:
    await user.skills.add(skill)


async def remove_skill(user: User, skill: Skill) -> None:
    await user.skills.remove(skill)


async def get_company_profile(user_id: int) -> CompanyProfile | None:
    return await CompanyProfile.filter(user_id=user_id).first()


async def update_company_profile(profile: CompanyProfile, data: dict) -> CompanyProfile:
    await profile.update_from_dict(data).save()
    return profile


async def get_student_profile(user_id: int) -> StudentProfile | None:
    return await StudentProfile.filter(user_id=user_id).first()


async def update_student_profile(profile: StudentProfile, data: dict) -> StudentProfile:
    await profile.update_from_dict(data).save()
    return profile


async def get_all_users(skip: int = 0, limit: int = 20) -> list[User]:
    return await User.all().offset(skip).limit(limit)
