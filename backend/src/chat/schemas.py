from datetime import datetime
from typing import Optional
from pydantic import BaseModel


class ChatRoomResponse(BaseModel):
    id: str
    project_id: int
    project_title: str
    participants: list[int]
    last_message: Optional[str] = None
    last_message_at: Optional[datetime] = None
    created_at: datetime


class ChatMessageResponse(BaseModel):
    id: str
    room_id: str
    sender_id: int
    sender_name: str
    content: str
    created_at: datetime


class SendMessageRequest(BaseModel):
    content: str
