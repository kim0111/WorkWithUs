from src.skills.models import Skill


async def get_all_skills() -> list[Skill]:
    return await Skill.all().order_by("name")


async def get_skill_by_name(name: str) -> Skill | None:
    return await Skill.filter(name=name).first()


async def create_skill(name: str, category: str | None = None) -> Skill:
    return await Skill.create(name=name, category=category)
