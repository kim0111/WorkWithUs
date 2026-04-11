import enum
from tortoise import fields, models


class RoleEnum(str, enum.Enum):
    student = "student"
    company = "company"
    committee = "committee"
    admin = "admin"


class User(models.Model):
    id = fields.IntField(primary_key=True)
    email = fields.CharField(max_length=255, unique=True, db_index=True)
    username = fields.CharField(max_length=100, unique=True, db_index=True)
    hashed_password = fields.CharField(max_length=255)
    full_name = fields.CharField(max_length=255, null=True)
    role = fields.CharEnumField(enum_type=RoleEnum, default=RoleEnum.student)
    avatar_url = fields.CharField(max_length=500, null=True)
    bio = fields.TextField(null=True)
    is_active = fields.BooleanField(default=True)
    is_blocked = fields.BooleanField(default=False)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    skills = fields.ManyToManyField(
        "models.Skill", related_name="users", through="user_skills"
    )

    class Meta:
        table = "users"


class CompanyProfile(models.Model):
    id = fields.IntField(primary_key=True)
    user = fields.OneToOneField("models.User", related_name="company_profile", on_delete=fields.CASCADE)
    company_name = fields.CharField(max_length=255)
    industry = fields.CharField(max_length=255, null=True)
    website = fields.CharField(max_length=500, null=True)
    description = fields.TextField(null=True)
    location = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "company_profiles"


class StudentProfile(models.Model):
    id = fields.IntField(primary_key=True)
    user = fields.OneToOneField("models.User", related_name="student_profile", on_delete=fields.CASCADE)
    university = fields.CharField(max_length=255, null=True)
    major = fields.CharField(max_length=255, null=True)
    graduation_year = fields.IntField(null=True)
    gpa = fields.FloatField(null=True)
    resume_url = fields.CharField(max_length=500, null=True)
    rating = fields.FloatField(default=0.0)
    completed_projects_count = fields.IntField(default=0)

    class Meta:
        table = "student_profiles"
