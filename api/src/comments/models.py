from tortoise import fields
from tortoise.models import Model


class Comment(Model):
    id = fields.UUIDField(pk=True)
    application = fields.ForeignKeyField("models.Application", related_name="comments")
    author = fields.ForeignKeyField("models.User", related_name="comments")
    body = fields.TextField()
    parent = fields.ForeignKeyField("models.Comment", related_name="replies", null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "comments"
