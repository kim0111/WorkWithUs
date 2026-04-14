from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from src.teams.models import TeamRole


class TeamMemberAdd(BaseModel):
    user_id: int
    role: TeamRole = TeamRole.other


class TeamMemberUpdate(BaseModel):
    role: Optional[TeamRole] = None
    is_lead: Optional[bool] = None


class TeamMemberResponse(BaseModel):
    id: int
    project_id: int
    user_id: int
    username: str = ""
    full_name: Optional[str] = None
    role: TeamRole
    is_lead: bool
    joined_at: datetime

    class Config:
        from_attributes = True
