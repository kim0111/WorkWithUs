from uuid import UUID

from fastapi import APIRouter, Depends

from src.auth.dependencies import get_current_user
from src.comments import service
from src.comments.schemas import CommentCreate, CommentRead
from src.users.models import User

router = APIRouter()


@router.post("", response_model=CommentRead, status_code=201)
async def create_comment(
    application_id: UUID,
    body: CommentCreate,
    user: User = Depends(get_current_user),
):
    return await service.create_comment(application_id, body, user)


@router.get("", response_model=list[CommentRead])
async def list_comments(
    application_id: UUID,
    user: User = Depends(get_current_user),
):
    return await service.list_comments(application_id, user)
