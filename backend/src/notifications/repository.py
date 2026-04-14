from datetime import datetime, timezone
from bson import ObjectId
from src.database.mongodb import get_mongodb


async def insert_notification(user_id: int, title: str, message: str,
                              notification_type: str, link: str | None) -> None:
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


async def find_notifications(user_id: int, unread_only: bool,
                             skip: int, limit: int) -> list[dict]:
    db = await get_mongodb()
    query: dict = {"user_id": user_id}
    if unread_only:
        query["is_read"] = False
    cursor = db.notifications.find(query).sort("created_at", -1).skip(skip).limit(limit)
    return [doc async for doc in cursor]


async def mark_read(notification_id: str, user_id: int) -> dict | None:
    db = await get_mongodb()
    return await db.notifications.find_one_and_update(
        {"_id": ObjectId(notification_id), "user_id": user_id, "is_read": False},
        {"$set": {"is_read": True}},
        return_document=True,
    )


async def mark_all_read(user_id: int) -> None:
    db = await get_mongodb()
    await db.notifications.update_many(
        {"user_id": user_id, "is_read": False},
        {"$set": {"is_read": True}},
    )
