from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from bson import ObjectId
from fastapi import APIRouter, Depends, Query
from src.database.mongodb import get_mongodb
from src.core.dependencies import get_current_user
from src.core.redis import incr_counter, get_counter, reset_counter
from src.users.models import User


# ── Schemas ──────────────────────────────────────────

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


# ── Helper: create notification (call from other services) ──

async def create_notification(user_id: int, title: str, message: str = "",
                               notification_type: str = "info", link: str = None):
    db = await get_mongodb()
    doc = {
        "user_id": user_id,
        "title": title,
        "message": message,
        "is_read": False,
        "notification_type": notification_type,
        "link": link,
        "created_at": datetime.now(timezone.utc),
    }
    await db.notifications.insert_one(doc)
    await incr_counter(f"unread:{user_id}")


# ── Router ───────────────────────────────────────────

router = APIRouter(prefix="/notifications", tags=["Notifications"])


@router.get("/", response_model=list[NotificationResponse])
async def get_notifications(
    unread_only: bool = Query(False),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=100),
    current_user: User = Depends(get_current_user),
):
    db = await get_mongodb()
    query = {"user_id": current_user.id}
    if unread_only:
        query["is_read"] = False

    skip = (page - 1) * size
    cursor = db.notifications.find(query).sort("created_at", -1).skip(skip).limit(size)

    items = []
    async for doc in cursor:
        items.append(NotificationResponse(
            id=str(doc["_id"]),
            title=doc["title"],
            message=doc.get("message"),
            is_read=doc["is_read"],
            notification_type=doc.get("notification_type", "info"),
            link=doc.get("link"),
            created_at=doc["created_at"],
        ))
    return items


@router.get("/unread-count", response_model=UnreadCountResponse)
async def get_unread_count(current_user: User = Depends(get_current_user)):
    count = await get_counter(f"unread:{current_user.id}")
    return UnreadCountResponse(count=count)


@router.put("/{notification_id}/read", response_model=NotificationResponse)
async def mark_as_read(notification_id: str, current_user: User = Depends(get_current_user)):
    db = await get_mongodb()
    result = await db.notifications.find_one_and_update(
        {"_id": ObjectId(notification_id), "user_id": current_user.id, "is_read": False},
        {"$set": {"is_read": True}},
        return_document=True,
    )
    if not result:
        from fastapi import HTTPException
        raise HTTPException(status_code=404, detail="Notification not found or already read")

    # Decrement unread counter
    r = await get_counter(f"unread:{current_user.id}")
    if r > 0:
        from src.core.redis import get_redis
        redis = await get_redis()
        await redis.decr(f"unread:{current_user.id}")

    return NotificationResponse(
        id=str(result["_id"]), title=result["title"],
        message=result.get("message"), is_read=True,
        notification_type=result.get("notification_type", "info"),
        link=result.get("link"), created_at=result["created_at"],
    )


@router.post("/read-all", status_code=204)
async def mark_all_read(current_user: User = Depends(get_current_user)):
    db = await get_mongodb()
    await db.notifications.update_many(
        {"user_id": current_user.id, "is_read": False},
        {"$set": {"is_read": True}},
    )
    await reset_counter(f"unread:{current_user.id}")
