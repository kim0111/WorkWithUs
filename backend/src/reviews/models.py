from tortoise import fields, models


class Review(models.Model):
    id = fields.IntField(pk=True)
    reviewer = fields.ForeignKeyField("models.User", related_name="reviews_given", on_delete=fields.CASCADE)
    reviewee = fields.ForeignKeyField("models.User", related_name="reviews_received", on_delete=fields.CASCADE)
    project = fields.ForeignKeyField("models.Project", related_name="reviews", on_delete=fields.CASCADE)
    application = fields.ForeignKeyField(
        "models.Application", related_name="reviews", on_delete=fields.CASCADE, null=True
    )
    rating = fields.FloatField()
    comment = fields.TextField(null=True)
    review_type = fields.CharField(max_length=50, null=True)
    created_at = fields.DatetimeField(auto_now_add=True)

    class Meta:
        table = "reviews"
