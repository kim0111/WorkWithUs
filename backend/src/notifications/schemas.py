from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class NotificationResponse(BaseModel):
    id: str
    title: str
    message: Optional[str] = None
    is_read: bool
    notification_type: str = "info"
    link: Optional[str] = None
    created_at: datetime


class UnreadCountResponse(BaseModel):
    count: int
