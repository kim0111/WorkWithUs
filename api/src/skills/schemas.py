from pydantic import BaseModel


class SkillRead(BaseModel):
    id: int
    name: str


class SkillCreate(BaseModel):
    name: str
