from tortoise import fields
from tortoise.models import Model


class FileAttachment(Model):
    id = fields.UUIDField(pk=True)
    project = fields.ForeignKeyField("models.Project", related_name="files")
    uploaded_by = fields.ForeignKeyField("models.User", related_name="uploaded_files")
    original_filename = fields.CharField(max_length=512)
    storage_key = fields.CharField(max_length=1024, unique=True)
    content_type = fields.CharField(max_length=255)
    size_bytes = fields.BigIntField()
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "file_attachments"
