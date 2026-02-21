import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.postgres import get_db
from src.database.mongodb import get_mongodb
from src.core.dependencies import get_current_user
from src.core.security import decode_token
from src.core.redis import publish_message, get_redis
from src.core.email import send_chat_notification_email
from src.users.models import User
from src.users.repository import UserRepository

logger = logging.getLogger(__name__)


# ── Schemas ──────────────────────────────────────────

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


# ── Connection Manager (in-process) ─────────────────

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}  # room_id -> [ws, ...]

    async def connect(self, room_id: str, ws: WebSocket):
        await ws.accept()
        if room_id not in self.active:
            self.active[room_id] = []
        self.active[room_id].append(ws)

    def disconnect(self, room_id: str, ws: WebSocket):
        if room_id in self.active:
            self.active[room_id] = [w for w in self.active[room_id] if w != ws]

    async def broadcast(self, room_id: str, message: dict):
        for ws in self.active.get(room_id, []):
            try:
                await ws.send_json(message)
            except Exception:
                pass


manager = ConnectionManager()


# ── Helper ───────────────────────────────────────────

async def get_or_create_room(project_id: int, participant_ids: list[int], project_title: str) -> dict:
    db = await get_mongodb()
    room = await db.chat_rooms.find_one({
        "project_id": project_id,
        "participants": {"$all": participant_ids}
    })
    if not room:
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


# ── REST Router ──────────────────────────────────────

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/rooms/{project_id}/{other_user_id}", response_model=ChatRoomResponse)
async def create_or_get_room(project_id: int, other_user_id: int,
                              db: AsyncSession = Depends(get_db),
                              current_user: User = Depends(get_current_user)):
    """Create or get existing chat room for a project between two users."""
    from src.projects.router import ProjectRepository
    project = await ProjectRepository(db).get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user_repo = UserRepository(db)
    other = await user_repo.get_by_id(other_user_id)
    if not other:
        raise HTTPException(status_code=404, detail="User not found")

    room = await get_or_create_room(project_id, [current_user.id, other_user_id], project.title)
    return ChatRoomResponse(
        id=str(room["_id"]),
        project_id=room["project_id"],
        project_title=room.get("project_title", ""),
        participants=room["participants"],
        last_message=room.get("last_message"),
        last_message_at=room.get("last_message_at"),
        created_at=room["created_at"],
    )


@router.get("/rooms", response_model=list[ChatRoomResponse])
async def get_my_rooms(current_user: User = Depends(get_current_user)):
    """Get all chat rooms for current user."""
    mongo = await get_mongodb()
    cursor = mongo.chat_rooms.find({"participants": current_user.id}).sort("last_message_at", -1)
    rooms = []
    async for room in cursor:
        rooms.append(ChatRoomResponse(
            id=str(room["_id"]),
            project_id=room["project_id"],
            project_title=room.get("project_title", ""),
            participants=room["participants"],
            last_message=room.get("last_message"),
            last_message_at=room.get("last_message_at"),
            created_at=room["created_at"],
        ))
    return rooms


@router.get("/rooms/{room_id}/messages", response_model=list[ChatMessageResponse])
async def get_messages(room_id: str, page: int = Query(1, ge=1), size: int = Query(50, ge=1, le=100),
                       current_user: User = Depends(get_current_user)):
    """Get paginated messages for a room."""
    mongo = await get_mongodb()
    room = await mongo.chat_rooms.find_one({"_id": ObjectId(room_id)})
    if not room or current_user.id not in room["participants"]:
        raise HTTPException(status_code=403, detail="Not a participant")

    skip = (page - 1) * size
    cursor = mongo.chat_messages.find({"room_id": room_id}).sort("created_at", -1).skip(skip).limit(size)
    messages = []
    async for msg in cursor:
        messages.append(ChatMessageResponse(
            id=str(msg["_id"]), room_id=msg["room_id"],
            sender_id=msg["sender_id"], sender_name=msg["sender_name"],
            content=msg["content"], created_at=msg["created_at"],
        ))
    return list(reversed(messages))


@router.post("/rooms/{room_id}/messages", response_model=ChatMessageResponse, status_code=201)
async def send_message_rest(room_id: str, data: SendMessageRequest, bg: BackgroundTasks,
                            db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
    """Send a message via REST (alternative to WebSocket)."""
    mongo = await get_mongodb()
    room = await mongo.chat_rooms.find_one({"_id": ObjectId(room_id)})
    if not room or current_user.id not in room["participants"]:
        raise HTTPException(status_code=403, detail="Not a participant")

    msg = {
        "room_id": room_id,
        "sender_id": current_user.id,
        "sender_name": current_user.full_name or current_user.username,
        "content": data.content,
        "created_at": datetime.now(timezone.utc),
    }
    result = await mongo.chat_messages.insert_one(msg)
    msg["_id"] = result.inserted_id

    # Update room
    await mongo.chat_rooms.update_one(
        {"_id": ObjectId(room_id)},
        {"$set": {"last_message": data.content[:100], "last_message_at": msg["created_at"]}}
    )

    # Broadcast via Redis pub/sub
    broadcast_data = {
        "id": str(msg["_id"]), "room_id": room_id,
        "sender_id": current_user.id, "sender_name": msg["sender_name"],
        "content": data.content, "created_at": msg["created_at"].isoformat(),
    }
    await publish_message(f"chat:{room_id}", broadcast_data)
    await manager.broadcast(room_id, broadcast_data)

    # Email notification to other participant
    other_ids = [p for p in room["participants"] if p != current_user.id]
    for uid in other_ids:
        user_repo = UserRepository(db)
        other = await user_repo.get_by_id(uid)
        if other:
            bg.add_task(send_chat_notification_email, other.email, other.username,
                        msg["sender_name"], room.get("project_title", ""))

    return ChatMessageResponse(
        id=str(msg["_id"]), room_id=room_id,
        sender_id=current_user.id, sender_name=msg["sender_name"],
        content=data.content, created_at=msg["created_at"],
    )


# ── WebSocket ────────────────────────────────────────

@router.websocket("/ws/{room_id}")
async def websocket_chat(ws: WebSocket, room_id: str):
    """WebSocket endpoint for real-time chat."""
    # Authenticate via query param
    token = ws.query_params.get("token")
    if not token:
        await ws.close(code=4001, reason="Token required")
        return

    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
        sender_name = payload.get("username", f"User {user_id}")
    except Exception:
        await ws.close(code=4001, reason="Invalid token")
        return

    # Verify room access
    mongo = await get_mongodb()
    room = await mongo.chat_rooms.find_one({"_id": ObjectId(room_id)})
    if not room or user_id not in room["participants"]:
        await ws.close(code=4003, reason="Not a participant")
        return

    await manager.connect(room_id, ws)

    # Also subscribe to Redis pub/sub for multi-instance support
    redis = await get_redis()
    pubsub = redis.pubsub()
    await pubsub.subscribe(f"chat:{room_id}")

    async def redis_listener():
        try:
            async for message in pubsub.listen():
                if message["type"] == "message":
                    data = json.loads(message["data"])
                    if data.get("sender_id") != user_id:
                        try:
                            await ws.send_json(data)
                        except Exception:
                            break
        except asyncio.CancelledError:
            pass

    listener_task = asyncio.create_task(redis_listener())

    try:
        while True:
            data = await ws.receive_json()
            content = data.get("content", "").strip()
            if not content:
                continue

            msg = {
                "room_id": room_id,
                "sender_id": user_id,
                "sender_name": sender_name,
                "content": content,
                "created_at": datetime.now(timezone.utc),
            }
            result = await mongo.chat_messages.insert_one(msg)

            await mongo.chat_rooms.update_one(
                {"_id": ObjectId(room_id)},
                {"$set": {"last_message": content[:100], "last_message_at": msg["created_at"]}}
            )

            broadcast = {
                "id": str(result.inserted_id), "room_id": room_id,
                "sender_id": user_id, "sender_name": sender_name,
                "content": content, "created_at": msg["created_at"].isoformat(),
            }
            await manager.broadcast(room_id, broadcast)
            await publish_message(f"chat:{room_id}", broadcast)

    except WebSocketDisconnect:
        pass
    except Exception as e:
        logger.error(f"WebSocket error: {e}")
    finally:
        manager.disconnect(room_id, ws)
        listener_task.cancel()
        await pubsub.unsubscribe(f"chat:{room_id}")
        await pubsub.close()
