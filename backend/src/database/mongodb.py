from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase
from typing import Optional
from src.core.config import settings

_client: Optional[AsyncIOMotorClient] = None
_db: Optional[AsyncIOMotorDatabase] = None


async def get_mongodb() -> AsyncIOMotorDatabase:
    global _client, _db
    if _client is None:
        _client = AsyncIOMotorClient(settings.MONGODB_URL)
        _db = _client[settings.MONGODB_DB_NAME]
    return _db


async def close_mongodb():
    global _client, _db
    if _client:
        _client.close()
        _client = None
        _db = None


async def init_mongodb():
    """Create indexes for collections."""
    db = await get_mongodb()

    # Chat messages indexes
    await db.chat_messages.create_index([("room_id", 1), ("created_at", -1)])
    await db.chat_messages.create_index([("sender_id", 1)])

    # Chat rooms
    await db.chat_rooms.create_index([("participants", 1)])
    await db.chat_rooms.create_index([("project_id", 1)])

    # Activity logs
    await db.activity_logs.create_index([("user_id", 1), ("created_at", -1)])
    await db.activity_logs.create_index([("action", 1)])
    await db.activity_logs.create_index([("created_at", -1)])

    # Notifications
    await db.notifications.create_index([("user_id", 1), ("is_read", 1), ("created_at", -1)])
