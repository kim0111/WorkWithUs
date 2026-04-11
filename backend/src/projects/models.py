import enum
from tortoise import fields, models


class ProjectStatus(str, enum.Enum):
    open = "open"
    in_progress = "in_progress"
    closed = "closed"


class Project(models.Model):
    id = fields.IntField(pk=True)
    title = fields.CharField(max_length=255)
    description = fields.TextField()
    owner = fields.ForeignKeyField("models.User", related_name="owned_projects", on_delete=fields.CASCADE)
    status = fields.CharEnumField(enum_type=ProjectStatus, default=ProjectStatus.open)
    max_participants = fields.IntField(default=1)
    deadline = fields.DatetimeField(null=True)
    is_student_project = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    required_skills = fields.ManyToManyField(
        "models.Skill", related_name="projects", through="project_skills"
    )

    class Meta:
        table = "projects"


class ProjectFile(models.Model):
    id = fields.IntField(pk=True)
    project = fields.ForeignKeyField("models.Project", related_name="attachments", on_delete=fields.CASCADE)
    uploader = fields.ForeignKeyField("models.User", related_name="uploaded_files", on_delete=fields.CASCADE)
    filename = fields.CharField(max_length=500)
    object_name = fields.CharField(max_length=500)
    file_size = fields.IntField(null=True)
    content_type = fields.CharField(max_length=255, null=True)
    file_type = fields.CharField(max_length=50, default="attachment")
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "project_files"
