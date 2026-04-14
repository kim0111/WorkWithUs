from src.teams.models import ProjectTeam, TeamRole


async def get_by_id(member_id: int) -> ProjectTeam | None:
    return await ProjectTeam.filter(id=member_id).first()


async def get_by_project_and_user(project_id: int, user_id: int) -> ProjectTeam | None:
    return await ProjectTeam.filter(project_id=project_id, user_id=user_id).first()


async def get_project_team(project_id: int) -> list[ProjectTeam]:
    return await ProjectTeam.filter(project_id=project_id).order_by("-is_lead", "joined_at")


async def get_user_memberships(user_id: int) -> list[ProjectTeam]:
    return await ProjectTeam.filter(user_id=user_id).order_by("-joined_at")


async def add_member(project_id: int, user_id: int, role: TeamRole,
                     is_lead: bool = False) -> ProjectTeam:
    return await ProjectTeam.create(
        project_id=project_id, user_id=user_id, role=role, is_lead=is_lead,
    )


async def remove_member(project_id: int, user_id: int) -> bool:
    deleted = await ProjectTeam.filter(project_id=project_id, user_id=user_id).delete()
    return deleted > 0


async def update_member(member: ProjectTeam) -> None:
    await member.save()


async def has_lead(project_id: int) -> bool:
    return await ProjectTeam.filter(project_id=project_id, is_lead=True).exists()


async def count_members(project_id: int) -> int:
    return await ProjectTeam.filter(project_id=project_id).count()
