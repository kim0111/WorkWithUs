from datetime import datetime, timezone
from bson import ObjectId
from src.database.mongodb import get_mongodb


async def find_room(project_id: int, participant_ids: list[int]) -> dict | None:
    db = await get_mongodb()
    return await db.chat_rooms.find_one({
        "project_id": project_id,
        "participants": {"$all": participant_ids},
    })


async def create_room(project_id: int, participant_ids: list[int],
                      project_title: str) -> dict:
    db = await get_mongodb()
    room = {
        "project_id": project_id,
        "project_title": project_title,
        "participants": sorted(participant_ids),
        "last_message": None,
        "last_message_at": None,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.chat_rooms.insert_one(room)
    room["_id"] = result.inserted_id
    return room


async def get_room_by_id(room_id: str) -> dict | None:
    db = await get_mongodb()
    return await db.chat_rooms.find_one({"_id": ObjectId(room_id)})


async def get_rooms_for_user(user_id: int) -> list[dict]:
    db = await get_mongodb()
    cursor = db.chat_rooms.find({"participants": user_id}).sort("last_message_at", -1)
    return [room async for room in cursor]


async def get_messages(room_id: str, skip: int, limit: int) -> list[dict]:
    db = await get_mongodb()
    cursor = db.chat_messages.find({"room_id": room_id}).sort("created_at", -1).skip(skip).limit(limit)
    return [msg async for msg in cursor]


async def insert_message(room_id: str, sender_id: int, sender_name: str,
                         content: str) -> dict:
    db = await get_mongodb()
    msg = {
        "room_id": room_id,
        "sender_id": sender_id,
        "sender_name": sender_name,
        "content": content,
        "created_at": datetime.now(timezone.utc),
    }
    result = await db.chat_messages.insert_one(msg)
    msg["_id"] = result.inserted_id
    return msg


async def update_room_last_message(room_id: str, content: str,
                                   timestamp: datetime) -> None:
    db = await get_mongodb()
    await db.chat_rooms.update_one(
        {"_id": ObjectId(room_id)},
        {"$set": {"last_message": content[:100], "last_message_at": timestamp}},
    )
