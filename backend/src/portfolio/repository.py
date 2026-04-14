from src.portfolio.models import PortfolioItem
from src.users.models import StudentProfile


async def get_student_profile(user_id: int) -> StudentProfile | None:
    return await StudentProfile.filter(user_id=user_id).first()


async def get_items_by_student(student_id: int) -> list[PortfolioItem]:
    return await PortfolioItem.filter(student_id=student_id).order_by("-created_at")


async def get_item_by_id(item_id: int) -> PortfolioItem | None:
    return await PortfolioItem.filter(id=item_id).first()


async def create_item(student_id: int, title: str, description: str | None,
                      project_url: str | None, image_url: str | None) -> PortfolioItem:
    return await PortfolioItem.create(
        student_id=student_id, title=title, description=description,
        project_url=project_url, image_url=image_url,
    )


async def delete_item(item: PortfolioItem) -> None:
    await item.delete()
