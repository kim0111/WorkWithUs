from fastapi import HTTPException
from src.chat import repository
from src.chat.schemas import ChatRoomResponse, ChatMessageResponse
from src.core.redis import publish_message
from src.projects.models import Project
from src.users.models import User


def _room_to_response(room: dict) -> ChatRoomResponse:
    return ChatRoomResponse(
        id=str(room["_id"]),
        project_id=room["project_id"],
        project_title=room.get("project_title", ""),
        participants=room["participants"],
        last_message=room.get("last_message"),
        last_message_at=room.get("last_message_at"),
        created_at=room["created_at"],
    )


def _msg_to_response(msg: dict) -> ChatMessageResponse:
    return ChatMessageResponse(
        id=str(msg["_id"]),
        room_id=msg["room_id"],
        sender_id=msg["sender_id"],
        sender_name=msg["sender_name"],
        content=msg["content"],
        created_at=msg["created_at"],
    )


async def get_or_create_room(project_id: int, current_user_id: int,
                             other_user_id: int) -> ChatRoomResponse:
    project = await Project.filter(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    other = await User.filter(id=other_user_id).first()
    if not other:
        raise HTTPException(status_code=404, detail="User not found")

    participant_ids = [current_user_id, other_user_id]
    room = await repository.find_room(project_id, participant_ids)
    if not room:
        room = await repository.create_room(project_id, participant_ids, project.title)
    return _room_to_response(room)


async def get_my_rooms(user_id: int) -> list[ChatRoomResponse]:
    rooms = await repository.get_rooms_for_user(user_id)
    return [_room_to_response(r) for r in rooms]


async def get_messages(room_id: str, user_id: int, page: int,
                       size: int) -> list[ChatMessageResponse]:
    room = await repository.get_room_by_id(room_id)
    if not room or user_id not in room["participants"]:
        raise HTTPException(status_code=403, detail="Not a participant")

    skip = (page - 1) * size
    messages = await repository.get_messages(room_id, skip, size)
    return list(reversed([_msg_to_response(m) for m in messages]))


async def send_message(room_id: str, user: User, content: str, broadcast_fn=None) -> tuple[ChatMessageResponse, dict]:
    room = await repository.get_room_by_id(room_id)
    if not room or user.id not in room["participants"]:
        raise HTTPException(status_code=403, detail="Not a participant")

    sender_name = user.full_name or user.username
    msg = await repository.insert_message(room_id, user.id, sender_name, content)
    await repository.update_room_last_message(room_id, content, msg["created_at"])

    broadcast_data = {
        "id": str(msg["_id"]), "room_id": room_id,
        "sender_id": user.id, "sender_name": sender_name,
        "content": content, "created_at": msg["created_at"].isoformat(),
    }
    await publish_message(f"chat:{room_id}", broadcast_data)
    if broadcast_fn:
        await broadcast_fn(room_id, broadcast_data)

    other_ids = [p for p in room["participants"] if p != user.id]
    return _msg_to_response(msg), {"room": room, "other_ids": other_ids}
