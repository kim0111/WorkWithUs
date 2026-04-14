import enum
from tortoise import fields, models


class TeamRole(str, enum.Enum):
    lead = "lead"
    frontend = "frontend"
    backend = "backend"
    designer = "designer"
    pm = "pm"
    qa = "qa"
    other = "other"


class ProjectTeam(models.Model):
    id = fields.IntField(primary_key=True)
    project = fields.ForeignKeyField("models.Project", related_name="team_members", on_delete=fields.CASCADE)
    user = fields.ForeignKeyField("models.User", related_name="team_memberships", on_delete=fields.CASCADE)
    role = fields.CharEnumField(enum_type=TeamRole, default=TeamRole.other)
    is_lead = fields.BooleanField(default=False)
    joined_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "project_teams"
        unique_together = (("project", "user"),)
