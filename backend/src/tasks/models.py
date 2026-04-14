import enum
from tortoise import fields, models


class TaskStatus(str, enum.Enum):
    todo = "todo"
    in_progress = "in_progress"
    review = "review"
    done = "done"


class TaskPriority(str, enum.Enum):
    low = "low"
    medium = "medium"
    high = "high"


class Task(models.Model):
    id = fields.IntField(primary_key=True)
    project = fields.ForeignKeyField("models.Project", related_name="tasks", on_delete=fields.CASCADE)
    title = fields.CharField(max_length=255)
    description = fields.TextField(default="")
    status = fields.CharEnumField(enum_type=TaskStatus, default=TaskStatus.todo)
    priority = fields.CharEnumField(enum_type=TaskPriority, default=TaskPriority.medium)
    assignee = fields.ForeignKeyField("models.User", related_name="assigned_tasks",
                                      null=True, on_delete=fields.SET_NULL)
    deadline = fields.DatetimeField(null=True)
    created_by = fields.ForeignKeyField("models.User", related_name="created_tasks",
                                        on_delete=fields.CASCADE)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "tasks"


class TaskComment(models.Model):
    id = fields.IntField(primary_key=True)
    task = fields.ForeignKeyField("models.Task", related_name="comments", on_delete=fields.CASCADE)
    author = fields.ForeignKeyField("models.User", related_name="task_comments", on_delete=fields.CASCADE)
    content = fields.TextField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "task_comments"


class TaskActivity(models.Model):
    id = fields.IntField(primary_key=True)
    task = fields.ForeignKeyField("models.Task", related_name="activities", on_delete=fields.CASCADE)
    actor = fields.ForeignKeyField("models.User", related_name="task_activities", on_delete=fields.CASCADE)
    action = fields.CharField(max_length=50)
    from_value = fields.CharField(max_length=255, null=True)
    to_value = fields.CharField(max_length=255, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "task_activities"
