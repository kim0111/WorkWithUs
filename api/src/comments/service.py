from uuid import UUID

from fastapi import HTTPException, status

from src.applications.models import Application
from src.comments.models import Comment
from src.comments.schemas import CommentCreate, CommentRead
from src.projects.models import Project
from src.users.models import User


async def _check_access(application: Application, user: User) -> None:
    project = await Project.get(id=application.project_id)
    if application.student_id != user.id and project.company_id != user.id:
        raise HTTPException(status_code=status.HTTP_403_FORBIDDEN, detail="Access denied")


def _comment_to_read(c: Comment) -> CommentRead:
    return CommentRead(
        id=c.id,
        application_id=c.application_id,
        author_id=c.author_id,
        body=c.body,
        parent_id=c.parent_id,
        created_at=c.created_at,
    )


async def create_comment(application_id: UUID, data: CommentCreate, user: User) -> CommentRead:
    application = await Application.get_or_none(id=application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    await _check_access(application, user)

    if data.parent_id:
        parent = await Comment.get_or_none(id=data.parent_id, application_id=application_id)
        if not parent:
            raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Parent comment not found")

    comment = await Comment.create(
        application=application,
        author=user,
        body=data.body,
        parent_id=data.parent_id,
    )
    return _comment_to_read(comment)


async def list_comments(application_id: UUID, user: User) -> list[CommentRead]:
    application = await Application.get_or_none(id=application_id)
    if not application:
        raise HTTPException(status_code=status.HTTP_404_NOT_FOUND, detail="Application not found")
    await _check_access(application, user)

    all_comments = await Comment.filter(application_id=application_id).order_by("created_at")

    comment_map: dict[UUID, CommentRead] = {}
    roots: list[CommentRead] = []

    for c in all_comments:
        cr = _comment_to_read(c)
        comment_map[cr.id] = cr

    for c in all_comments:
        cr = comment_map[c.id]
        if c.parent_id and c.parent_id in comment_map:
            comment_map[c.parent_id].replies.append(cr)
        else:
            roots.append(cr)

    return roots
