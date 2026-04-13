from tortoise.functions import Avg, Count
from src.reviews.models import Review


async def get_review(reviewer_id: int, project_id: int, review_type: str) -> Review | None:
    return await Review.filter(
        reviewer_id=reviewer_id, project_id=project_id, review_type=review_type,
    ).first()


async def create_review(reviewer_id: int, reviewee_id: int, project_id: int,
                        application_id: int | None, rating: float,
                        comment: str | None, review_type: str) -> Review:
    return await Review.create(
        reviewer_id=reviewer_id, reviewee_id=reviewee_id,
        project_id=project_id, application_id=application_id,
        rating=rating, comment=comment, review_type=review_type,
    )


async def get_reviews_for_user(user_id: int, offset: int, limit: int) -> list[Review]:
    return await Review.filter(reviewee_id=user_id).order_by("-created_at").offset(offset).limit(limit)


async def get_user_rating(user_id: int) -> dict:
    result = await Review.filter(reviewee_id=user_id).annotate(
        avg_rating=Avg("rating"), total=Count("id"),
    ).values("avg_rating", "total")
    if result:
        return {"avg": result[0]["avg_rating"] or 0.0, "total": result[0]["total"] or 0}
    return {"avg": 0.0, "total": 0}
