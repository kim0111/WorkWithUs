import enum

from tortoise import fields
from tortoise.models import Model


class UserRole(str, enum.Enum):
    STUDENT = "student"
    COMPANY = "company"
    ADMIN = "admin"


class User(Model):
    id = fields.UUIDField(pk=True)
    email = fields.CharField(max_length=255, unique=True)
    hashed_password = fields.CharField(max_length=255)
    role = fields.CharEnumField(UserRole)
    is_active = fields.BooleanField(default=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "users"


class StudentProfile(Model):
    id = fields.UUIDField(pk=True)
    user = fields.OneToOneField("models.User", related_name="student_profile")
    first_name = fields.CharField(max_length=100, default="")
    last_name = fields.CharField(max_length=100, default="")
    university = fields.CharField(max_length=255, default="")
    faculty = fields.CharField(max_length=255, default="")
    year_of_study = fields.IntField(null=True)
    bio = fields.TextField(default="")
    skills = fields.ManyToManyField(
        "models.Skill", related_name="students", through="student_skills"
    )

    class Meta:
        table = "student_profiles"


class CompanyProfile(Model):
    id = fields.UUIDField(pk=True)
    user = fields.OneToOneField("models.User", related_name="company_profile")
    company_name = fields.CharField(max_length=255, default="")
    description = fields.TextField(default="")
    website = fields.CharField(max_length=255, default="")
    contact_person = fields.CharField(max_length=255, default="")

    class Meta:
        table = "company_profiles"
