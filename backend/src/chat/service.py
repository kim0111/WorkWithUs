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

    # Heal legacy messages whose sender_name was stored as a placeholder like
    # "User 5" when the WebSocket path did not have the username on the JWT.
    unknown_ids = {
        m["sender_id"] for m in messages
        if not m.get("sender_name") or m["sender_name"] == f"User {m['sender_id']}"
    }
    name_map: dict[int, str] = {}
    if unknown_ids:
        users = await User.filter(id__in=list(unknown_ids)).only("id", "username", "full_name")
        name_map = {u.id: (u.full_name or u.username) for u in users}

    responses = []
    for m in messages:
        if m["sender_id"] in name_map:
            m = {**m, "sender_name": name_map[m["sender_id"]]}
        responses.append(_msg_to_response(m))
    return list(reversed(responses))


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


async def get_or_create_team_room(project_id: int, user_id: int) -> ChatRoomResponse:
    project = await Project.filter(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    from src.teams import repository as teams_repo
    members = await teams_repo.get_project_team(project_id)
    member_ids = [m.user_id for m in members]

    if user_id not in member_ids and project.owner_id != user_id:
        raise HTTPException(status_code=403, detail="Not a team member or project owner")

    participant_ids = list(set(member_ids + [project.owner_id]))
    room = await repository.find_team_room(project_id)
    if not room:
        room = await repository.create_team_room(project_id, participant_ids, project.title)
    else:
        for pid in participant_ids:
            if pid not in room["participants"]:
                await repository.add_room_participant(str(room["_id"]), pid)
        room = await repository.get_room_by_id(str(room["_id"]))
    return _room_to_response(room)
