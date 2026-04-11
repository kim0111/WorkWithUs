from tortoise import fields, models


class PortfolioItem(models.Model):
    id = fields.IntField(pk=True)
    student = fields.ForeignKeyField(
        "models.StudentProfile", related_name="portfolio_items", on_delete=fields.CASCADE
    )
    title = fields.CharField(max_length=255)
    description = fields.TextField(null=True)
    project_url = fields.CharField(max_length=500, null=True)
    image_url = fields.CharField(max_length=500, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "portfolio_items"
