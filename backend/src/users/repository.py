from tortoise.expressions import Q
from tortoise.functions import Count
from src.users.models import User, CompanyProfile, StudentProfile
from src.skills.models import Skill
from src.applications.models import Application, ApplicationStatus


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


async def search_students(skill_ids: list[int] | None, min_rating: float | None,
                          available: bool, q_str: str | None,
                          offset: int, limit: int) -> tuple[list[User], int]:
    qs = User.filter(role="student", is_active=True, is_blocked=False)

    if q_str:
        qs = qs.filter(Q(username__icontains=q_str) | Q(full_name__icontains=q_str))

    if skill_ids:
        unique_skill_ids = list(set(skill_ids))
        matching_ids = await User.filter(
            skills__id__in=unique_skill_ids,
        ).annotate(skill_match_count=Count("skills__id", distinct=True)).filter(
            skill_match_count__gte=len(unique_skill_ids),
        ).values_list("id", flat=True)
        qs = qs.filter(id__in=list(set(matching_ids)))

    if min_rating is not None:
        qs = qs.filter(student_profile__rating__gte=min_rating)

    if available:
        active_statuses = (
            ApplicationStatus.accepted, ApplicationStatus.in_progress,
            ApplicationStatus.submitted, ApplicationStatus.revision_requested,
            ApplicationStatus.approved,
        )
        busy_ids = await Application.filter(
            status__in=active_statuses,
        ).values_list("applicant_id", flat=True)
        if busy_ids:
            qs = qs.exclude(id__in=list(set(busy_ids)))

    total = await qs.count()
    items = await qs.prefetch_related("skills", "student_profile").offset(offset).limit(limit)
    return items, total


async def active_app_exists_for(user_id: int) -> bool:
    active = (ApplicationStatus.accepted, ApplicationStatus.in_progress,
              ApplicationStatus.submitted, ApplicationStatus.revision_requested,
              ApplicationStatus.approved)
    return await Application.filter(applicant_id=user_id, status__in=active).exists()
