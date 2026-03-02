import enum

from tortoise import fields
from tortoise.models import Model


class ApplicationStatus(str, enum.Enum):
    PENDING = "pending"
    ACCEPTED = "accepted"
    REJECTED = "rejected"


class Application(Model):
    id = fields.UUIDField(pk=True)
    project = fields.ForeignKeyField("models.Project", related_name="applications")
    student = fields.ForeignKeyField("models.User", related_name="applications")
    cover_letter = fields.TextField(default="")
    status = fields.CharEnumField(ApplicationStatus, default=ApplicationStatus.PENDING)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "applications"
        unique_together = (("project", "student"),)
