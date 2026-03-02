from uuid import UUID

from fastapi import HTTPException, status
from tortoise.expressions import Q

from src.projects.models import Project, ProjectStatus
from src.projects.schemas import (
    ProjectCreate,
    ProjectListRead,
    ProjectRead,
    ProjectUpdate,
)
from src.skills.models import Skill
from src.skills.schemas import SkillRead
from src.users.models import User


async def _project_to_read(project: Project) -> ProjectRead:
    await project.fetch_related("required_skills")
    return ProjectRead(
        id=project.id,
        company_id=project.company_id,
        title=project.title,
        description=project.description,
        status=project.status,
        deadline=project.deadline,
        required_skills=[SkillRead(id=s.id, name=s.name) for s in project.required_skills],
        created_at=project.created_at,
        updated_at=project.updated_at,
    )


async def _project_to_list_read(project: Project) -> ProjectListRead:
    await project.fetch_related("required_skills")
    return ProjectListRead(
        id=project.id,
        company_id=project.company_id,
        title=project.title,
        status=project.status,
        deadline=project.deadline,
        required_skills=[SkillRead(id=s.id, name=s.name) for s in project.required_skills],
        created_at=project.created_at,
    )


async def create_project(data: ProjectCreate, company: User) -> ProjectRead:
    project = await Project.create(
        company=company,
        title=data.title,
        description=data.description,
        deadline=data.deadline,
    )
    if data.required_skill_ids:
        skills = await Skill.filter(id__in=data.required_skill_ids)
        await project.required_skills.add(*skills)
    return await _project_to_read(project)


async def list_projects(
    status_filter: ProjectStatus | None = None,
    skill_id: int | None = None,
    search: str | None = None,
) -> list[ProjectListRead]:
    qs = Project.filter(status=ProjectStatus.PUBLISHED)
    if status_filter:
        qs = Project.filter(status=status_filter)
    if skill_id:
        qs = qs.filter(required_skills__id=skill_id)
    if search:
        qs = qs.filter(Q(title__icontains=search) | Q(description__icontains=search))
    projects = await qs.order_by("-created_at").distinct()
    return [await _project_to_list_read(p) for p in projects]


async def list_my_projects(company: User) -> list[ProjectListRead]:
    projects = await Project.filter(company=company).order_by("-created_at")
    return [await _project_to_list_read(p) for p in projects]


async def get_project(project_id: UUID) -> ProjectRead:
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return await _project_to_read(project)


async def get_project_model(project_id: UUID) -> Project:
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    return project


async def update_project(project_id: UUID, data: ProjectUpdate, company: User) -> ProjectRead:
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the project owner")

    update_data = data.model_dump(exclude_unset=True)
    skill_ids = update_data.pop("required_skill_ids", None)

    for field, value in update_data.items():
        setattr(project, field, value)
    await project.save()

    if skill_ids is not None:
        await project.required_skills.clear()
        if skill_ids:
            skills = await Skill.filter(id__in=skill_ids)
            await project.required_skills.add(*skills)

    return await _project_to_read(project)


async def delete_project(project_id: UUID, company: User) -> None:
    project = await Project.get_or_none(id=project_id)
    if not project:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Project not found")
    if project.company_id != company.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Not the project owner")
    if project.status != ProjectStatus.DRAFT:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Only draft projects can be deleted",
        )
    await project.delete()
