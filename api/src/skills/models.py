from tortoise import fields
from tortoise.models import Model


class Skill(Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)

    students: fields.ManyToManyRelation

    class Meta:
        table = "skills"
