from tortoise.queryset import Q, QuerySet
from src.projects.models import Project, ProjectStatus
from src.skills.models import Skill


def build_filter(status: ProjectStatus | None = None, owner_id: int | None = None,
                 is_student_project: bool | None = None, search: str | None = None,
                 skill_ids: list[int] | None = None) -> QuerySet:
    filters = {}
    if status:
        filters["status"] = status
    if owner_id:
        filters["owner_id"] = owner_id
    if is_student_project is not None:
        filters["is_student_project"] = is_student_project
    q = Project.filter(**filters)
    if skill_ids:
        q = q.filter(required_skills__id__in=skill_ids)
    if search:
        q = q.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(required_skills__name__icontains=search)
        )
    return q


async def get_by_id(project_id: int) -> Project | None:
    return await Project.filter(id=project_id).prefetch_related("required_skills", "attachments").first()


async def create_project(title: str, description: str, owner_id: int,
                         max_participants: int, deadline, is_student_project: bool,
                         skill_ids: list[int]) -> Project:
    project = await Project.create(
        title=title, description=description, owner_id=owner_id,
        max_participants=max_participants, deadline=deadline,
        is_student_project=is_student_project,
    )
    if skill_ids:
        skills = await Skill.filter(id__in=skill_ids)
        await project.required_skills.add(*skills)
    await project.fetch_related("required_skills", "attachments")
    return project


async def update_project(project: Project, data: dict) -> Project:
    await project.update_from_dict(data).save()
    return project


async def delete_project(project: Project) -> None:
    await project.delete()
