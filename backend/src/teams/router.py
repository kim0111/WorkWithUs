from fastapi import APIRouter, Depends
from src.core.dependencies import get_current_user
from src.users.models import User
from src.teams import service
from src.teams.schemas import TeamMemberAdd, TeamMemberUpdate, TeamMemberResponse

router = APIRouter(prefix="/teams", tags=["Teams"])


@router.get("/project/{project_id}", response_model=list[TeamMemberResponse])
async def get_project_team(project_id: int,
                           current_user: User = Depends(get_current_user)):
    return await service.get_project_team(project_id)


@router.get("/my", response_model=list[TeamMemberResponse])
async def get_my_teams(current_user: User = Depends(get_current_user)):
    return await service.get_my_teams(current_user)


@router.post("/project/{project_id}/members", response_model=TeamMemberResponse, status_code=201)
async def add_team_member(project_id: int, data: TeamMemberAdd,
                          current_user: User = Depends(get_current_user)):
    return await service.add_member(project_id, data.user_id, data.role, current_user)


@router.put("/project/{project_id}/members/{user_id}", response_model=TeamMemberResponse)
async def update_team_member(project_id: int, user_id: int, data: TeamMemberUpdate,
                             current_user: User = Depends(get_current_user)):
    return await service.update_member(project_id, user_id, data.role, data.is_lead, current_user)


@router.delete("/project/{project_id}/members/{user_id}", status_code=204)
async def remove_team_member(project_id: int, user_id: int,
                             current_user: User = Depends(get_current_user)):
    await service.remove_member(project_id, user_id, current_user)
