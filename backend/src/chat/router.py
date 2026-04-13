import json
import asyncio
import logging
from datetime import datetime, timezone
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from src.core.dependencies import get_current_user
from src.core.security import decode_token
from src.core.redis import get_redis
from src.core.email import send_chat_notification_email
from src.users.models import User
from src.chat import repository, service
from src.chat.schemas import ChatRoomResponse, ChatMessageResponse, SendMessageRequest

logger = logging.getLogger(__name__)


# ── Connection Manager (in-process) ─────────────────

class ConnectionManager:
    def __init__(self):
        self.active: dict[str, list[WebSocket]] = {}

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


# ── REST Router ──────────────────────────────────────

router = APIRouter(prefix="/chat", tags=["Chat"])


@router.post("/rooms/{project_id}/{other_user_id}", response_model=ChatRoomResponse)
async def create_or_get_room(project_id: int, other_user_id: int,
                              current_user: User = Depends(get_current_user)):
    return await service.get_or_create_room(project_id, current_user.id, other_user_id)


@router.get("/rooms", response_model=list[ChatRoomResponse])
async def get_my_rooms(current_user: User = Depends(get_current_user)):
    return await service.get_my_rooms(current_user.id)


@router.get("/rooms/{room_id}/messages", response_model=list[ChatMessageResponse])
async def get_messages(room_id: str, page: int = Query(1, ge=1),
                       size: int = Query(50, ge=1, le=100),
                       current_user: User = Depends(get_current_user)):
    return await service.get_messages(room_id, current_user.id, page, size)


@router.post("/rooms/{room_id}/messages", response_model=ChatMessageResponse, status_code=201)
async def send_message_rest(room_id: str, data: SendMessageRequest, bg: BackgroundTasks,
                            current_user: User = Depends(get_current_user)):
    msg_response, ctx = await service.send_message(
        room_id, current_user, data.content, manager.broadcast,
    )

    for uid in ctx["other_ids"]:
        other = await User.filter(id=uid).first()
        if other:
            bg.add_task(send_chat_notification_email, other.email, other.username,
                        current_user.full_name or current_user.username,
                        ctx["room"].get("project_title", ""))
    return msg_response


# ── WebSocket ────────────────────────────────────────

@router.websocket("/ws/{room_id}")
async def websocket_chat(ws: WebSocket, room_id: str):
    """WebSocket endpoint for real-time chat.
    Authentication: send {"type": "auth", "token": "<jwt>"} as the first message.
    Falls back to query param ?token= for backwards compatibility.
    """
    await ws.accept()

    token = ws.query_params.get("token")
    if not token:
        try:
            auth_msg = await asyncio.wait_for(ws.receive_json(), timeout=10.0)
            if auth_msg.get("type") != "auth" or not auth_msg.get("token"):
                await ws.close(code=4001, reason="First message must be {type: 'auth', token: '<jwt>'}")
                return
            token = auth_msg["token"]
        except (asyncio.TimeoutError, Exception):
            await ws.close(code=4001, reason="Authentication timeout")
            return

    try:
        payload = decode_token(token)
        user_id = int(payload["sub"])
        sender_name = payload.get("username", f"User {user_id}")
    except Exception:
        await ws.close(code=4001, reason="Invalid token")
        return

    room = await repository.get_room_by_id(room_id)
    if not room or user_id not in room["participants"]:
        await ws.close(code=4003, reason="Not a participant")
        return

    if room_id not in manager.active:
        manager.active[room_id] = []
    manager.active[room_id].append(ws)

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
        mongo = await repository.get_room_by_id(room_id)  # noqa: just for db ref
        while True:
            data = await ws.receive_json()
            content = data.get("content", "").strip()
            if not content:
                continue

            msg = await repository.insert_message(room_id, user_id, sender_name, content)
            await repository.update_room_last_message(room_id, content, msg["created_at"])

            broadcast = {
                "id": str(msg["_id"]), "room_id": room_id,
                "sender_id": user_id, "sender_name": sender_name,
                "content": content, "created_at": msg["created_at"].isoformat(),
            }
            await manager.broadcast(room_id, broadcast)
            from src.core.redis import publish_message
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
