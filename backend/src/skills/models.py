from tortoise import fields, models


class Skill(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    category = fields.CharField(max_length=100, null=True)

    class Meta:
        table = "skills"
