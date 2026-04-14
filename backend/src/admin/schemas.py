from typing import Optional
from pydantic import BaseModel
from src.users.models import RoleEnum


class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None
    role: Optional[RoleEnum] = None


class StatsResponse(BaseModel):
    total_users: int
    total_students: int
    total_companies: int
    total_projects: int
    total_applications: int
    active_projects: int
    total_chat_messages: int = 0
    total_notifications: int = 0
