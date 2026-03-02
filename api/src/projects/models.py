import enum

from tortoise import fields
from tortoise.models import Model


class ProjectStatus(str, enum.Enum):
    DRAFT = "draft"
    PUBLISHED = "published"
    CLOSED = "closed"


class Project(Model):
    id = fields.UUIDField(pk=True)
    company = fields.ForeignKeyField("models.User", related_name="projects")
    title = fields.CharField(max_length=255)
    description = fields.TextField(default="")
    status = fields.CharEnumField(ProjectStatus, default=ProjectStatus.DRAFT)
    deadline = fields.DatetimeField(null=True)
    required_skills = fields.ManyToManyField(
        "models.Skill", related_name="projects", through="project_required_skills"
    )
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "projects"
