from sqlalchemy import Column, Integer, String
from sqlalchemy.orm import relationship
from src.database.postgres import Base
from src.users.models import user_skills


class Skill(Base):
    __tablename__ = "skills"
    id = Column(Integer, primary_key=True, index=True)
    name = Column(String(100), unique=True, nullable=False)
    category = Column(String(100))
    users = relationship("User", secondary=user_skills, back_populates="skills")
    projects = relationship("Project", secondary="project_skills", back_populates="required_skills")
