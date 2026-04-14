from fastapi import HTTPException
from src.reviews import repository
from src.reviews.models import Review
from src.reviews.schemas import UserRatingResponse, ReviewResponse
from src.users.models import User
from src.projects.models import Project
from src.applications.models import Application, ApplicationStatus
from src.notifications.service import create_notification
from src.teams import repository as teams_repo


async def _enrich(review: Review) -> ReviewResponse:
    reviewer = await User.filter(id=review.reviewer_id).only(
        "id", "username", "full_name", "role").first()
    reviewee = await User.filter(id=review.reviewee_id).only(
        "id", "username", "full_name").first()
    project = await Project.filter(id=review.project_id).only("id", "title").first()
    return ReviewResponse(
        id=review.id,
        reviewer_id=review.reviewer_id,
        reviewee_id=review.reviewee_id,
        reviewer_username=reviewer.username if reviewer else None,
        reviewer_full_name=reviewer.full_name if reviewer else None,
        reviewer_role=(reviewer.role.value if reviewer and reviewer.role else None),
        reviewee_username=reviewee.username if reviewee else None,
        reviewee_full_name=reviewee.full_name if reviewee else None,
        project_id=review.project_id,
        project_title=project.title if project else None,
        application_id=review.application_id,
        rating=review.rating,
        comment=review.comment,
        review_type=review.review_type,
        created_at=review.created_at,
    )


async def create_review(reviewer: User, reviewee_id: int, project_id: int,
                        application_id: int | None, rating: float,
                        comment: str | None) -> Review:
    if reviewer.id == reviewee_id:
        raise HTTPException(status_code=400, detail="Cannot review yourself")

    project = await Project.filter(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    is_owner = project.owner_id == reviewer.id
    is_team_member = await teams_repo.get_by_project_and_user(project_id, reviewer.id)
    review_type = "owner_to_student" if is_owner else "student_to_owner"

    existing = await repository.get_review(reviewer.id, project_id, review_type, reviewee_id)
    if existing:
        raise HTTPException(status_code=400, detail="You already reviewed this user for this project")

    if not is_owner and not is_team_member:
        raise HTTPException(status_code=403, detail="Only project owner or team members can leave reviews")

    if application_id:
        app = await Application.filter(id=application_id).first()
        if not app or app.status not in (ApplicationStatus.approved, ApplicationStatus.completed):
            raise HTTPException(status_code=400, detail="Can only review after work is approved/completed")

    review = await repository.create_review(
        reviewer.id, reviewee_id, project_id, application_id, rating, comment, review_type,
    )

    reviewee = await User.filter(id=reviewee_id).first()
    if reviewee:
        await create_notification(
            reviewee_id, "New Review",
            f"{reviewer.username} left you a {rating}/5 review",
            notification_type="review", link=f"/profile/{reviewee_id}",
        )

    return await _enrich(review), reviewee


async def get_user_reviews(user_id: int, page: int, size: int) -> list[ReviewResponse]:
    offset = (page - 1) * size
    reviews = await repository.get_reviews_for_user(user_id, offset, size)
    return [await _enrich(r) for r in reviews]


async def get_user_rating(user_id: int) -> UserRatingResponse:
    data = await repository.get_user_rating(user_id)
    return UserRatingResponse(
        user_id=user_id,
        average_rating=round(float(data["avg"]), 2),
        total_reviews=int(data["total"]),
    )
