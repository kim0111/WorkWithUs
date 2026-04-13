from fastapi import HTTPException
from src.core.redis import incr_counter, get_counter, reset_counter, get_redis
from src.notifications import repository
from src.notifications.schemas import NotificationResponse, UnreadCountResponse


async def create_notification(user_id: int, title: str, message: str = "",
                              notification_type: str = "info", link: str = None):
    """Create a notification. Called from other modules (reviews, applications, etc.)."""
    await repository.insert_notification(user_id, title, message, notification_type, link)
    await incr_counter(f"unread:{user_id}")


def _doc_to_response(doc: dict) -> NotificationResponse:
    return NotificationResponse(
        id=str(doc["_id"]),
        title=doc["title"],
        message=doc.get("message"),
        is_read=doc["is_read"],
        notification_type=doc.get("notification_type", "info"),
        link=doc.get("link"),
        created_at=doc["created_at"],
    )


async def get_notifications(user_id: int, unread_only: bool, page: int,
                            size: int) -> list[NotificationResponse]:
    skip = (page - 1) * size
    docs = await repository.find_notifications(user_id, unread_only, skip, size)
    return [_doc_to_response(doc) for doc in docs]


async def get_unread_count(user_id: int) -> UnreadCountResponse:
    count = await get_counter(f"unread:{user_id}")
    return UnreadCountResponse(count=count)


async def mark_as_read(notification_id: str, user_id: int) -> NotificationResponse:
    result = await repository.mark_read(notification_id, user_id)
    if not result:
        raise HTTPException(status_code=404, detail="Notification not found or already read")

    count = await get_counter(f"unread:{user_id}")
    if count > 0:
        redis = await get_redis()
        await redis.decr(f"unread:{user_id}")

    return _doc_to_response(result)


async def mark_all_read(user_id: int) -> None:
    await repository.mark_all_read(user_id)
    await reset_counter(f"unread:{user_id}")
