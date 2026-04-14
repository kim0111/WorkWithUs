from fastapi import APIRouter, Depends, Query
from src.core.dependencies import get_current_user
from src.users.models import User
from src.notifications import service
from src.notifications.schemas import NotificationResponse, UnreadCountResponse

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=list[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    return await service.get_notifications(current_user.id, unread_only, page, size)


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(current_user: User = Depends(get_current_user)):
    return await service.get_unread_count(current_user.id)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(notification_id: str, current_user: User = Depends(get_current_user)):
    return await service.mark_as_read(notification_id, current_user.id)


@router.post("/read-all", status_code=204)
async def mark_all_read(current_user: User = Depends(get_current_user)):
    await service.mark_all_read(current_user.id)
