from src.skills.models import Skill
from src.skills.schemas import SkillCreate, SkillRead


async def list_skills() -> list[SkillRead]:
    skills = await Skill.all().order_by("name")
    return [SkillRead(id=s.id, name=s.name) for s in skills]


async def create_skill(data: SkillCreate) -> SkillRead:
    skill = await Skill.create(name=data.name)
    return SkillRead(id=skill.id, name=skill.name)
