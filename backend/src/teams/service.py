from fastapi import HTTPException
from src.teams import repository
from src.teams.models import ProjectTeam, TeamRole
from src.teams.schemas import TeamMemberResponse
from src.projects.models import Project
from src.users.models import User, RoleEnum
from src.notifications.service import create_notification


def _member_to_response(member: ProjectTeam, user: User) -> TeamMemberResponse:
    return TeamMemberResponse(
        id=member.id,
        project_id=member.project_id,
        user_id=member.user_id,
        username=user.username,
        full_name=user.full_name,
        role=member.role,
        is_lead=member.is_lead,
        joined_at=member.joined_at,
    )


async def get_project_team(project_id: int) -> list[TeamMemberResponse]:
    project = await Project.filter(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    members = await repository.get_project_team(project_id)
    result = []
    for m in members:
        user = await User.filter(id=m.user_id).first()
        if user:
            result.append(_member_to_response(m, user))
    return result


async def get_my_teams(user: User) -> list[TeamMemberResponse]:
    memberships = await repository.get_user_memberships(user.id)
    result = []
    for m in memberships:
        u = await User.filter(id=m.user_id).first()
        if u:
            result.append(_member_to_response(m, u))
    return result


async def add_member(project_id: int, user_id: int, role: TeamRole,
                     current_user: User) -> TeamMemberResponse:
    project = await Project.filter(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    is_owner = project.owner_id == current_user.id
    is_admin = current_user.role == RoleEnum.admin
    lead_membership = await repository.get_by_project_and_user(project_id, current_user.id)
    is_lead = lead_membership and lead_membership.is_lead

    if not (is_owner or is_admin or is_lead):
        raise HTTPException(status_code=403, detail="Only project owner, admin, or team lead can add members")

    target_user = await User.filter(id=user_id).first()
    if not target_user:
        raise HTTPException(status_code=404, detail="User not found")

    existing = await repository.get_by_project_and_user(project_id, user_id)
    if existing:
        raise HTTPException(status_code=400, detail="User is already a team member")

    count = await repository.count_members(project_id)
    if count >= project.max_participants:
        raise HTTPException(status_code=400, detail="Team has reached maximum size")

    member = await repository.add_member(project_id, user_id, role)

    await create_notification(
        user_id, "Team Invitation",
        f"You have been added to the team for project '{project.title}'",
        notification_type="team", link=f"/projects/{project_id}",
    )

    return _member_to_response(member, target_user)


async def remove_member(project_id: int, user_id: int,
                        current_user: User) -> None:
    project = await Project.filter(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    is_owner = project.owner_id == current_user.id
    is_admin = current_user.role == RoleEnum.admin
    lead_membership = await repository.get_by_project_and_user(project_id, current_user.id)
    is_lead = lead_membership and lead_membership.is_lead
    is_self = current_user.id == user_id

    if not (is_owner or is_admin or is_lead or is_self):
        raise HTTPException(status_code=403, detail="Not authorized to remove this member")

    member = await repository.get_by_project_and_user(project_id, user_id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")

    if member.is_lead and not (is_owner or is_admin):
        raise HTTPException(status_code=400, detail="Only project owner or admin can remove the team lead")

    await repository.remove_member(project_id, user_id)

    if not is_self:
        await create_notification(
            user_id, "Removed from Team",
            f"You have been removed from the team for project '{project.title}'",
            notification_type="team", link=f"/projects/{project_id}",
        )


async def update_member(project_id: int, user_id: int, role: TeamRole | None,
                        is_lead: bool | None, current_user: User) -> TeamMemberResponse:
    project = await Project.filter(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    is_owner = project.owner_id == current_user.id
    is_admin = current_user.role == RoleEnum.admin
    lead_membership = await repository.get_by_project_and_user(project_id, current_user.id)
    current_is_lead = lead_membership and lead_membership.is_lead

    if not (is_owner or is_admin or current_is_lead):
        raise HTTPException(status_code=403, detail="Not authorized to update team members")

    member = await repository.get_by_project_and_user(project_id, user_id)
    if not member:
        raise HTTPException(status_code=404, detail="Team member not found")

    if role is not None:
        member.role = role
    if is_lead is not None:
        if is_lead and not (is_owner or is_admin):
            raise HTTPException(status_code=403, detail="Only project owner or admin can assign lead")
        member.is_lead = is_lead

    await repository.update_member(member)

    target_user = await User.filter(id=user_id).first()
    return _member_to_response(member, target_user)
