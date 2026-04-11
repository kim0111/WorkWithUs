import enum
from tortoise import fields, models


class ApplicationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    in_progress = "in_progress"
    submitted = "submitted"
    revision_requested = "revision_requested"
    approved = "approved"
    completed = "completed"


class Application(models.Model):
    id = fields.IntField(primary_key=True)
    project = fields.ForeignKeyField("models.Project", related_name="applications", on_delete=fields.CASCADE)
    applicant = fields.ForeignKeyField("models.User", related_name="applications", on_delete=fields.CASCADE)
    cover_letter = fields.TextField(null=True)
    status = fields.CharEnumField(enum_type=ApplicationStatus, default=ApplicationStatus.pending)
    submission_note = fields.TextField(null=True)
    revision_note = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "applications"
        unique_together = (("project", "applicant"),)
