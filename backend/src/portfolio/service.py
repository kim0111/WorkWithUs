from fastapi import HTTPException
from src.portfolio import repository
from src.portfolio.models import PortfolioItem
from src.users.models import User, RoleEnum


async def add_item(user: User, title: str, description: str | None,
                   project_url: str | None, image_url: str | None) -> PortfolioItem:
    if user.role != RoleEnum.student:
        raise HTTPException(status_code=403, detail="Only students have portfolios")
    student = await repository.get_student_profile(user.id)
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return await repository.create_item(student.id, title, description, project_url, image_url)


async def get_portfolio(user_id: int) -> list[PortfolioItem]:
    student = await repository.get_student_profile(user_id)
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return await repository.get_items_by_student(student.id)


async def delete_item(item_id: int, user: User) -> None:
    item = await repository.get_item_by_id(item_id)
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    student = await repository.get_student_profile(user.id)
    if not student or item.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    await repository.delete_item(item)
