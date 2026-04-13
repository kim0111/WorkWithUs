from typing import Optional
from pydantic import BaseModel


class SkillCreate(BaseModel):
    name: str
    category: Optional[str] = None


class SkillResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None

    class Config:
        from_attributes = True
