from fastapi import HTTPException
from src.core.redis import cache_delete_pattern
from src.projects import repository
from src.projects.models import Project, ProjectStatus
from src.users.models import User, RoleEnum


def _attach_owner(project: Project) -> Project:
    """Expose the owner's display name (company name for companies) on the project."""
    owner = project.owner
    profile = getattr(owner, "company_profile", None)
    if profile and profile.company_name:
        project.owner_name = profile.company_name
    else:
        project.owner_name = owner.full_name or owner.username
    project.owner_avatar = owner.avatar_url
    return project


async def create_project(user: User, title: str, description: str,
                         max_participants: int, deadline, skill_ids: list[int],
                         is_student_project: bool) -> Project:
    if is_student_project and user.role != RoleEnum.student:
        raise HTTPException(status_code=403, detail="Only students can create student projects")
    if not is_student_project and user.role not in (RoleEnum.company, RoleEnum.admin):
        raise HTTPException(status_code=403, detail="Only companies can create company projects")

    if deadline and deadline.tzinfo is not None:
        deadline = deadline.replace(tzinfo=None)

    project = await repository.create_project(
        title, description, user.id, max_participants, deadline, is_student_project, skill_ids,
    )
    await cache_delete_pattern("projects:*")
    return _attach_owner(project)


async def list_projects(page: int, size: int, status: ProjectStatus | None,
                        owner_id: int | None, is_student_project: bool | None,
                        search: str | None, skill_ids: list[int] | None,
                        sort: str) -> dict:
    q = repository.build_filter(status, owner_id, is_student_project, search, skill_ids)
    total = await q.distinct().count()
    order = "deadline" if sort == "deadline" else "-created_at"
    items = await q.prefetch_related(
        "required_skills", "attachments", "owner__company_profile"
    ).distinct().order_by(order).offset((page - 1) * size).limit(size)
    return {"items": [_attach_owner(p) for p in items], "total": total, "page": page, "size": size}


async def get_project(project_id: int) -> Project:
    project = await repository.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return _attach_owner(project)


async def update_project(project_id: int, data: dict, user: User) -> Project:
    project = await repository.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != user.id and user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    await repository.update_project(project, data)
    await cache_delete_pattern("projects:*")
    return project


async def delete_project(project_id: int, user: User) -> None:
    project = await repository.get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != user.id and user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    await repository.delete_project(project)
    await cache_delete_pattern("projects:*")
