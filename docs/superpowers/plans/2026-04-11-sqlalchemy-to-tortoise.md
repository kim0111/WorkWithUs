# SQLAlchemy to Tortoise ORM Migration Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Replace SQLAlchemy with Tortoise ORM across the entire backend — models, queries, database setup, migrations, and tests.

**Architecture:** Bottom-up migration. Models and DB setup first, then remove the repository layer, update all routers/services to use Tortoise QuerySet API, replace Alembic with Aerich, and rewrite the test database setup.

**Tech Stack:** tortoise-orm[asyncpg], aerich, FastAPI, Pydantic v2

---

### Task 1: Update requirements.txt

**Files:**
- Modify: `backend/requirements.txt`

- [ ] **Step 1: Replace SQLAlchemy dependencies with Tortoise**

Replace the contents of `backend/requirements.txt` with:

```
fastapi==0.115.6
uvicorn[standard]==0.34.0
pydantic[email]==2.10.4
pydantic-settings==2.7.1
python-jose[cryptography]==3.3.0
passlib[bcrypt]==1.7.4
python-multipart==0.0.20

bcrypt==4.0.1

# ORM
tortoise-orm[asyncpg]==0.25.1
aerich==0.8.2

# MongoDB
motor==3.6.0
pymongo==4.9.2

# Redis
redis[hiredis]==5.2.1

# Async email
aiosmtplib==3.0.2

# MinIO
minio==7.2.12

# Testing
pytest==8.3.4
pytest-asyncio==0.24.0
pytest-cov==6.0.0
httpx==0.28.1
```

Removed: `sqlalchemy[asyncio]`, `asyncpg` (bundled in tortoise-orm[asyncpg]), `alembic`, `aiosqlite`.

- [ ] **Step 2: Install dependencies**

Run: `cd backend && pip install -r requirements.txt`
Expected: Successful install, tortoise-orm and aerich available.

- [ ] **Step 3: Commit**

```bash
git add backend/requirements.txt
git commit -m "chore: replace SQLAlchemy deps with tortoise-orm and aerich"
```

---

### Task 2: Rewrite database setup and config

**Files:**
- Rewrite: `backend/src/database/postgres.py`
- Modify: `backend/src/core/config.py`

- [ ] **Step 1: Rewrite `backend/src/database/postgres.py`**

Replace entire file with:

```python
from tortoise import Tortoise, connections
from src.core.config import settings


TORTOISE_ORM = {
    "connections": {"default": settings.DATABASE_URL},
    "apps": {
        "models": {
            "models": [
                "src.users.models",
                "src.skills.models",
                "src.projects.models",
                "src.applications.models",
                "src.reviews.models",
                "src.portfolio.models",
                "aerich.models",
            ],
            "default_connection": "default",
        }
    },
}


async def init_postgres():
    await Tortoise.init(config=TORTOISE_ORM)
    await Tortoise.generate_schemas()


async def close_postgres():
    await Tortoise.close_connections()
```

- [ ] **Step 2: Update `backend/src/core/config.py`**

Change the DATABASE_URL default from the SQLAlchemy format to Tortoise format. Replace:

```python
DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@postgres:5432/platform_db"
```

with:

```python
DATABASE_URL: str = "asyncpg://postgres:postgres@postgres:5432/platform_db"
```

Also update the `backend/.env` file — change:
```
DATABASE_URL=postgresql+asyncpg://postgres:postgres@postgres:5432/platform_db
```
to:
```
DATABASE_URL=asyncpg://postgres:postgres@postgres:5432/platform_db
```

- [ ] **Step 3: Commit**

```bash
git add backend/src/database/postgres.py backend/src/core/config.py backend/.env
git commit -m "feat: rewrite database setup for Tortoise ORM"
```

---

### Task 3: Rewrite all models

**Files:**
- Rewrite: `backend/src/users/models.py`
- Rewrite: `backend/src/skills/models.py`
- Rewrite: `backend/src/projects/models.py`
- Create: `backend/src/applications/models.py`
- Create: `backend/src/reviews/models.py`
- Create: `backend/src/portfolio/models.py`

- [ ] **Step 1: Rewrite `backend/src/users/models.py`**

Replace entire file with:

```python
import enum
from tortoise import fields, models


class RoleEnum(str, enum.Enum):
    student = "student"
    company = "company"
    committee = "committee"
    admin = "admin"


class User(models.Model):
    id = fields.IntField(pk=True)
    email = fields.CharField(max_length=255, unique=True, index=True)
    username = fields.CharField(max_length=100, unique=True, index=True)
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
    id = fields.IntField(pk=True)
    user = fields.OneToOneField("models.User", related_name="company_profile", on_delete=fields.CASCADE)
    company_name = fields.CharField(max_length=255)
    industry = fields.CharField(max_length=255, null=True)
    website = fields.CharField(max_length=500, null=True)
    description = fields.TextField(null=True)
    location = fields.CharField(max_length=255, null=True)

    class Meta:
        table = "company_profiles"


class StudentProfile(models.Model):
    id = fields.IntField(pk=True)
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
```

- [ ] **Step 2: Rewrite `backend/src/skills/models.py`**

Replace entire file with:

```python
from tortoise import fields, models


class Skill(models.Model):
    id = fields.IntField(pk=True)
    name = fields.CharField(max_length=100, unique=True)
    category = fields.CharField(max_length=100, null=True)

    class Meta:
        table = "skills"
```

Note: The M2M `users` and `projects` relationships are defined on the User and Project side respectively. Tortoise automatically creates the reverse relation via `related_name`.

- [ ] **Step 3: Rewrite `backend/src/projects/models.py`**

Replace entire file with:

```python
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
```

- [ ] **Step 4: Create `backend/src/applications/models.py`**

Create new file:

```python
import enum
from tortoise import fields, models


class ApplicationStatus(str, enum.Enum):
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    in_progress = "in_progress"
    submitted = "submitted"
    revision_requested = "revision_requested"
    approved = "approved"
    completed = "completed"


class Application(models.Model):
    id = fields.IntField(pk=True)
    project = fields.ForeignKeyField("models.Project", related_name="applications", on_delete=fields.CASCADE)
    applicant = fields.ForeignKeyField("models.User", related_name="applications", on_delete=fields.CASCADE)
    cover_letter = fields.TextField(null=True)
    status = fields.CharEnumField(enum_type=ApplicationStatus, default=ApplicationStatus.pending)
    submission_note = fields.TextField(null=True)
    revision_note = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)

    class Meta:
        table = "applications"
        unique_together = (("project", "applicant"),)
```

- [ ] **Step 5: Create `backend/src/reviews/models.py`**

Create new file:

```python
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
```

- [ ] **Step 6: Create `backend/src/portfolio/models.py`**

Create new file:

```python
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
```

- [ ] **Step 7: Commit**

```bash
git add backend/src/users/models.py backend/src/skills/models.py backend/src/projects/models.py \
  backend/src/applications/models.py backend/src/reviews/models.py backend/src/portfolio/models.py
git commit -m "feat: rewrite all models using Tortoise ORM"
```

---

### Task 4: Update core dependencies (get_current_user)

**Files:**
- Rewrite: `backend/src/core/dependencies.py`

- [ ] **Step 1: Rewrite `backend/src/core/dependencies.py`**

Replace entire file with:

```python
from fastapi import Depends, HTTPException, status
from fastapi.security import OAuth2PasswordBearer
from src.core.config import settings
from src.core.security import decode_token
from src.core.redis import is_token_blacklisted

oauth2_scheme = OAuth2PasswordBearer(tokenUrl=f"{settings.API_PREFIX}/auth/login")


async def get_current_user(
    token: str = Depends(oauth2_scheme),
):
    if await is_token_blacklisted(token):
        raise HTTPException(status_code=401, detail="Token has been revoked")

    payload = decode_token(token)
    if payload.get("type") != "access":
        raise HTTPException(status_code=401, detail="Invalid token type")

    from src.users.models import User
    user = await User.filter(id=int(payload["sub"])).prefetch_related("skills").first()
    if not user:
        raise HTTPException(status_code=401, detail="User not found")
    if user.is_blocked:
        raise HTTPException(status_code=403, detail="Account is blocked")
    return user


def require_role(*roles):
    async def checker(current_user=Depends(get_current_user)):
        if current_user.role not in roles:
            raise HTTPException(
                status_code=status.HTTP_403_FORBIDDEN,
                detail=f"Required roles: {[r.value for r in roles]}",
            )
        return current_user
    return checker
```

Key changes: removed `db: AsyncSession` parameter, removed `UserRepository` import, query Tortoise directly.

- [ ] **Step 2: Commit**

```bash
git add backend/src/core/dependencies.py
git commit -m "feat: update get_current_user to use Tortoise ORM directly"
```

---

### Task 5: Rewrite auth service and router

**Files:**
- Rewrite: `backend/src/auth/service.py`
- Modify: `backend/src/auth/router.py`

- [ ] **Step 1: Rewrite `backend/src/auth/service.py`**

Replace entire file with:

```python
from fastapi import HTTPException
from src.core.security import hash_password, verify_password, create_access_token, create_refresh_token, decode_token
from src.core.redis import blacklist_token
from src.users.models import User, CompanyProfile, StudentProfile, RoleEnum
from src.auth.schemas import RegisterRequest, TokenResponse
from src.core.activity import log_activity
from tortoise.transactions import in_transaction


class AuthService:
    async def register(self, data: RegisterRequest) -> User:
        if await User.filter(email=data.email).exists():
            raise HTTPException(status_code=400, detail="Email already registered")
        if await User.filter(username=data.username).exists():
            raise HTTPException(status_code=400, detail="Username already taken")

        async with in_transaction():
            user = await User.create(
                email=data.email, username=data.username,
                hashed_password=hash_password(data.password),
                full_name=data.full_name, role=data.role,
                is_active=False,
            )

            if data.role == RoleEnum.company:
                await CompanyProfile.create(user=user, company_name=data.username)
            elif data.role == RoleEnum.student:
                await StudentProfile.create(user=user)

        await user.fetch_related("skills")
        await log_activity(user.id, "register", f"Registered as {data.role.value}", "user", user.id)
        return user

    async def verify_email(self, user_id: int) -> User:
        user = await User.filter(id=user_id).prefetch_related("skills").first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        user.is_active = True
        await user.save()
        await log_activity(user_id, "email_verified", entity_type="user", entity_id=user_id)
        return user

    async def login(self, username: str, password: str) -> TokenResponse:
        user = await User.filter(username=username).first()
        if not user or not verify_password(password, user.hashed_password):
            raise HTTPException(status_code=401, detail="Invalid credentials")
        if not user.is_active:
            raise HTTPException(status_code=403, detail="Email not verified. Please check your inbox.")
        if user.is_blocked:
            raise HTTPException(status_code=403, detail="Account is blocked")

        await log_activity(user.id, "login", entity_type="user", entity_id=user.id)
        token_data = {"sub": str(user.id), "role": user.role.value}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    async def refresh(self, refresh_token: str) -> TokenResponse:
        payload = decode_token(refresh_token)
        if payload.get("type") != "refresh":
            raise HTTPException(status_code=401, detail="Invalid token type")
        user = await User.filter(id=int(payload["sub"])).first()
        if not user:
            raise HTTPException(status_code=401, detail="User not found")
        token_data = {"sub": str(user.id), "role": user.role.value}
        return TokenResponse(
            access_token=create_access_token(token_data),
            refresh_token=create_refresh_token(token_data),
        )

    async def logout(self, token: str):
        payload = decode_token(token)
        exp = payload.get("exp", 0)
        from datetime import datetime, timezone
        ttl = max(int(exp - datetime.now(timezone.utc).timestamp()), 1)
        await blacklist_token(token, ttl)
```

- [ ] **Step 2: Rewrite `backend/src/auth/router.py`**

Replace entire file with:

```python
import secrets
from fastapi import APIRouter, Depends, BackgroundTasks, Request, HTTPException
from fastapi.security import OAuth2PasswordRequestForm
from src.core.dependencies import get_current_user, oauth2_scheme
from src.core.email import send_verification_email, send_welcome_email
from src.core.redis import rate_limit_check, cache_set, cache_get, cache_delete
from src.users.models import User
from src.users.schemas import UserResponse
from src.auth.schemas import RegisterRequest, LoginRequest, TokenResponse, RefreshTokenRequest
from src.auth.service import AuthService

router = APIRouter(prefix="/auth", tags=["Authentication"])


@router.post("/register", response_model=UserResponse, status_code=201)
async def register(data: RegisterRequest, bg: BackgroundTasks):
    service = AuthService()
    user = await service.register(data)

    verify_token = secrets.token_urlsafe(32)
    await cache_set(f"email_verify:{verify_token}", str(user.id), ttl=86400)

    bg.add_task(send_verification_email, user.email, user.username, verify_token)
    return user


@router.get("/verify-email")
async def verify_email(token: str, bg: BackgroundTasks):
    user_id = await cache_get(f"email_verify:{token}")
    if not user_id:
        raise HTTPException(status_code=400, detail="Invalid or expired verification token")

    service = AuthService()
    user = await service.verify_email(int(user_id))
    await cache_delete(f"email_verify:{token}")

    bg.add_task(send_welcome_email, user.email, user.username)
    return {"message": "Email verified successfully"}


@router.post("/login", response_model=TokenResponse)
async def login(
    request: Request,
    form_data: OAuth2PasswordRequestForm = Depends(),
):
    client_ip = request.client.host if request.client else "unknown"
    if not await rate_limit_check(f"login:{client_ip}", max_requests=5, window=60):
        raise HTTPException(status_code=429, detail="Too many login attempts. Try again in 1 minute.")
    return await AuthService().login(form_data.username, form_data.password)


@router.post("/refresh", response_model=TokenResponse)
async def refresh(data: RefreshTokenRequest):
    return await AuthService().refresh(data.refresh_token)


@router.post("/logout", status_code=204)
async def logout(token: str = Depends(oauth2_scheme)):
    await AuthService().logout(token)


@router.get("/me", response_model=UserResponse)
async def get_me(current_user: User = Depends(get_current_user)):
    return current_user
```

Key changes: removed all `db: AsyncSession = Depends(get_db)` parameters, `AuthService()` is now stateless (no db arg).

- [ ] **Step 3: Commit**

```bash
git add backend/src/auth/service.py backend/src/auth/router.py
git commit -m "feat: rewrite auth service and router for Tortoise ORM"
```

---

### Task 6: Rewrite users service and router (delete repository)

**Files:**
- Delete: `backend/src/users/repository.py`
- Rewrite: `backend/src/users/service.py`
- Rewrite: `backend/src/users/router.py`

- [ ] **Step 1: Rewrite `backend/src/users/service.py`**

Replace entire file with:

```python
from typing import Sequence
from fastapi import HTTPException
from src.users.models import User, CompanyProfile, StudentProfile, RoleEnum
from src.users.schemas import UserUpdate
from src.core.redis import cache_get, cache_set, cache_delete


class UserService:
    async def get_user(self, user_id: int) -> User:
        cached = await cache_get(f"user:{user_id}")
        if cached:
            return cached

        user = await User.filter(id=user_id).prefetch_related("skills").first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        await cache_set(f"user:{user_id}", {
            "id": user.id, "email": user.email, "username": user.username,
            "full_name": user.full_name, "role": user.role.value,
            "avatar_url": user.avatar_url, "bio": user.bio,
            "is_active": user.is_active, "is_blocked": user.is_blocked,
        })
        return user

    async def update_user(self, user_id: int, data: UserUpdate, current_user: User) -> User:
        if current_user.id != user_id and current_user.role != RoleEnum.admin:
            raise HTTPException(status_code=403, detail="Not authorized")
        user = await User.filter(id=user_id).prefetch_related("skills").first()
        if not user:
            raise HTTPException(status_code=404, detail="User not found")
        update_data = data.model_dump(exclude_unset=True)
        await user.update_from_dict(update_data).save()
        await cache_delete(f"user:{user_id}")
        return user

    async def add_skill(self, user_id: int, skill_id: int, current_user: User):
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        from src.skills.models import Skill
        user = await User.filter(id=user_id).first()
        skill = await Skill.filter(id=skill_id).first()
        if not user or not skill:
            raise HTTPException(status_code=404, detail="User or skill not found")
        await user.skills.add(skill)
        await cache_delete(f"user:{user_id}")

    async def remove_skill(self, user_id: int, skill_id: int, current_user: User):
        if current_user.id != user_id:
            raise HTTPException(status_code=403, detail="Not authorized")
        from src.skills.models import Skill
        user = await User.filter(id=user_id).first()
        skill = await Skill.filter(id=skill_id).first()
        if not user or not skill:
            raise HTTPException(status_code=404, detail="User or skill not found")
        await user.skills.remove(skill)
        await cache_delete(f"user:{user_id}")

    async def get_all(self, skip: int = 0, limit: int = 20) -> Sequence[User]:
        return await User.all().offset(skip).limit(limit)
```

- [ ] **Step 2: Rewrite `backend/src/users/router.py`**

Replace entire file with:

```python
from fastapi import APIRouter, Depends, HTTPException
from src.core.dependencies import get_current_user
from src.users.models import User, CompanyProfile, StudentProfile, RoleEnum
from src.users.schemas import (
    UserResponse, UserUpdate,
    CompanyProfileCreate, CompanyProfileResponse,
    StudentProfileCreate, StudentProfileResponse,
)
from src.users.service import UserService

router = APIRouter(prefix="/users", tags=["Users"])


@router.get("/{user_id}", response_model=UserResponse)
async def get_user(user_id: int):
    return await UserService().get_user(user_id)


@router.put("/{user_id}", response_model=UserResponse)
async def update_user(user_id: int, data: UserUpdate,
                      current_user: User = Depends(get_current_user)):
    return await UserService().update_user(user_id, data, current_user)


@router.post("/{user_id}/skills/{skill_id}", status_code=204)
async def add_skill(user_id: int, skill_id: int,
                    current_user: User = Depends(get_current_user)):
    await UserService().add_skill(user_id, skill_id, current_user)


@router.delete("/{user_id}/skills/{skill_id}", status_code=204)
async def remove_skill(user_id: int, skill_id: int,
                       current_user: User = Depends(get_current_user)):
    await UserService().remove_skill(user_id, skill_id, current_user)


# -- Company Profile --

@router.get("/{user_id}/company-profile", response_model=CompanyProfileResponse)
async def get_company_profile(user_id: int):
    profile = await CompanyProfile.filter(user_id=user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    return profile


@router.put("/{user_id}/company-profile", response_model=CompanyProfileResponse)
async def update_company_profile(user_id: int, data: CompanyProfileCreate,
                                 current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    profile = await CompanyProfile.filter(user_id=user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Company profile not found")
    await profile.update_from_dict(data.model_dump(exclude_unset=True)).save()
    return profile


# -- Student Profile --

@router.get("/{user_id}/student-profile", response_model=StudentProfileResponse)
async def get_student_profile(user_id: int):
    profile = await StudentProfile.filter(user_id=user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return profile


@router.put("/{user_id}/student-profile", response_model=StudentProfileResponse)
async def update_student_profile(user_id: int, data: StudentProfileCreate,
                                 current_user: User = Depends(get_current_user)):
    if current_user.id != user_id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    profile = await StudentProfile.filter(user_id=user_id).first()
    if not profile:
        raise HTTPException(status_code=404, detail="Student profile not found")
    await profile.update_from_dict(data.model_dump(exclude_unset=True)).save()
    return profile
```

- [ ] **Step 3: Delete `backend/src/users/repository.py`**

```bash
rm backend/src/users/repository.py
```

- [ ] **Step 4: Commit**

```bash
git add backend/src/users/service.py backend/src/users/router.py
git rm backend/src/users/repository.py
git commit -m "feat: rewrite users service/router for Tortoise, delete repository layer"
```

---

### Task 7: Rewrite skills router

**Files:**
- Rewrite: `backend/src/skills/router.py`

- [ ] **Step 1: Rewrite `backend/src/skills/router.py`**

Replace entire file with:

```python
from typing import Optional, Sequence
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException
from src.core.dependencies import get_current_user
from src.core.redis import cache_get, cache_set, cache_delete
from src.skills.models import Skill


# -- Schemas --

class SkillCreate(BaseModel):
    name: str
    category: Optional[str] = None


class SkillResponse(BaseModel):
    id: int
    name: str
    category: Optional[str] = None
    class Config:
        from_attributes = True


# -- Router --

router = APIRouter(prefix="/skills", tags=["Skills"])


@router.get("/", response_model=list[SkillResponse])
async def get_all_skills():
    cached = await cache_get("skills:all")
    if cached:
        return [SkillResponse(id=s["id"], name=s["name"], category=s.get("category")) for s in cached]
    skills = await Skill.all().order_by("name")
    await cache_set("skills:all", [{"id": s.id, "name": s.name, "category": s.category} for s in skills])
    return skills


@router.post("/", response_model=SkillResponse, status_code=201)
async def create_skill(data: SkillCreate, _=Depends(get_current_user)):
    if await Skill.filter(name=data.name).exists():
        raise HTTPException(status_code=400, detail="Skill already exists")
    skill = await Skill.create(name=data.name, category=data.category)
    await cache_delete("skills:all")
    return skill
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/skills/router.py
git commit -m "feat: rewrite skills router for Tortoise ORM"
```

---

### Task 8: Rewrite projects router

**Files:**
- Rewrite: `backend/src/projects/router.py`

- [ ] **Step 1: Rewrite `backend/src/projects/router.py`**

Replace entire file with:

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, Query
from src.core.dependencies import get_current_user
from src.core.redis import cache_get, cache_set, cache_delete_pattern
from src.users.models import User, RoleEnum
from src.users.schemas import SkillOut
from src.projects.models import Project, ProjectStatus, ProjectFile
from src.skills.models import Skill
from tortoise.functions import Count


# -- Schemas --

class ProjectFileResponse(BaseModel):
    id: int
    filename: str
    object_name: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    file_type: str
    created_at: datetime
    class Config:
        from_attributes = True


class ProjectCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: str = Field(..., min_length=10)
    max_participants: int = Field(default=1, ge=1)
    deadline: Optional[datetime] = None
    skill_ids: list[int] = []
    is_student_project: bool = False


class ProjectUpdate(BaseModel):
    title: Optional[str] = None
    description: Optional[str] = None
    status: Optional[ProjectStatus] = None
    max_participants: Optional[int] = None
    deadline: Optional[datetime] = None


class ProjectResponse(BaseModel):
    id: int
    title: str
    description: str
    owner_id: int
    status: ProjectStatus
    max_participants: int
    deadline: Optional[datetime] = None
    is_student_project: bool
    required_skills: list[SkillOut] = []
    attachments: list[ProjectFileResponse] = []
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


class ProjectListResponse(BaseModel):
    items: list[ProjectResponse]
    total: int
    page: int
    size: int


# -- Helper --

def _build_project_filter(status=None, owner_id=None, is_student_project=None, search=None):
    filters = {}
    if status:
        filters["status"] = status
    if owner_id:
        filters["owner_id"] = owner_id
    if is_student_project is not None:
        filters["is_student_project"] = is_student_project
    q = Project.filter(**filters)
    if search:
        q = q.filter(title__icontains=search)
    return q


# -- Router --

router = APIRouter(prefix="/projects", tags=["Projects"])


@router.post("/", response_model=ProjectResponse, status_code=201)
async def create_project(data: ProjectCreate, current_user: User = Depends(get_current_user)):
    if data.is_student_project and current_user.role != RoleEnum.student:
        raise HTTPException(status_code=403, detail="Only students can create student projects")
    if not data.is_student_project and current_user.role not in (RoleEnum.company, RoleEnum.admin):
        raise HTTPException(status_code=403, detail="Only companies can create company projects")

    deadline = data.deadline
    if deadline and deadline.tzinfo is not None:
        deadline = deadline.replace(tzinfo=None)

    project = await Project.create(
        title=data.title, description=data.description, owner_id=current_user.id,
        max_participants=data.max_participants, deadline=deadline,
        is_student_project=data.is_student_project,
    )
    if data.skill_ids:
        skills = await Skill.filter(id__in=data.skill_ids)
        await project.required_skills.add(*skills)
    await project.fetch_related("required_skills", "attachments")
    await cache_delete_pattern("projects:*")
    return project


@router.get("/", response_model=ProjectListResponse)
async def list_projects(
    page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
    status: Optional[ProjectStatus] = None, owner_id: Optional[int] = None,
    is_student_project: Optional[bool] = None, search: Optional[str] = None,
):
    skip = (page - 1) * size
    q = _build_project_filter(status, owner_id, is_student_project, search)
    total = await q.count()
    items = await q.prefetch_related("required_skills", "attachments").order_by("-created_at").offset(skip).limit(size)
    return {"items": items, "total": total, "page": page, "size": size}


@router.get("/{project_id}", response_model=ProjectResponse)
async def get_project(project_id: int):
    project = await Project.filter(id=project_id).prefetch_related("required_skills", "attachments").first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    return project


@router.put("/{project_id}", response_model=ProjectResponse)
async def update_project(project_id: int, data: ProjectUpdate,
                         current_user: User = Depends(get_current_user)):
    project = await Project.filter(id=project_id).prefetch_related("required_skills", "attachments").first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    await project.update_from_dict(data.model_dump(exclude_unset=True)).save()
    await cache_delete_pattern("projects:*")
    return project


@router.delete("/{project_id}", status_code=204)
async def delete_project(project_id: int, current_user: User = Depends(get_current_user)):
    project = await Project.filter(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    await project.delete()
    await cache_delete_pattern("projects:*")
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/projects/router.py
git commit -m "feat: rewrite projects router for Tortoise ORM"
```

---

### Task 9: Rewrite applications router

**Files:**
- Rewrite: `backend/src/applications/router.py`

- [ ] **Step 1: Rewrite `backend/src/applications/router.py`**

Replace entire file with:

```python
from datetime import datetime
from typing import Optional, Sequence
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from src.core.dependencies import get_current_user
from src.core.email import send_application_status_email, send_new_application_email, send_submission_email
from src.core.activity import log_activity
from src.users.models import User, RoleEnum
from src.projects.models import Project
from src.applications.models import Application, ApplicationStatus


# -- Schemas --

class ApplicationCreate(BaseModel):
    project_id: int
    cover_letter: Optional[str] = None


class ApplicationUpdateStatus(BaseModel):
    status: ApplicationStatus
    note: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    project_id: int
    applicant_id: int
    cover_letter: Optional[str] = None
    status: ApplicationStatus
    submission_note: Optional[str] = None
    revision_note: Optional[str] = None
    created_at: datetime
    updated_at: datetime
    class Config:
        from_attributes = True


# -- Transition validation --

VALID_TRANSITIONS = {
    ApplicationStatus.pending: [ApplicationStatus.accepted, ApplicationStatus.rejected],
    ApplicationStatus.accepted: [ApplicationStatus.in_progress],
    ApplicationStatus.in_progress: [ApplicationStatus.submitted],
    ApplicationStatus.submitted: [ApplicationStatus.approved, ApplicationStatus.revision_requested],
    ApplicationStatus.revision_requested: [ApplicationStatus.submitted],
    ApplicationStatus.approved: [ApplicationStatus.completed],
}


# -- Router --

router = APIRouter(prefix="/applications", tags=["Applications"])


@router.post("/", response_model=ApplicationResponse, status_code=201)
async def apply(data: ApplicationCreate, bg: BackgroundTasks,
                current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.student:
        raise HTTPException(status_code=403, detail="Only students can apply")

    project = await Project.filter(id=data.project_id).prefetch_related("applications").first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.status.value != "open":
        raise HTTPException(status_code=400, detail="Project is not open")
    if await Application.filter(project_id=data.project_id, applicant_id=current_user.id).exists():
        raise HTTPException(status_code=400, detail="Already applied")

    active_statuses = (
        ApplicationStatus.accepted, ApplicationStatus.in_progress,
        ApplicationStatus.submitted, ApplicationStatus.approved, ApplicationStatus.completed,
    )
    active_count = await Application.filter(project_id=data.project_id, status__in=active_statuses).count()
    if active_count >= project.max_participants:
        raise HTTPException(status_code=400, detail="Project has reached maximum number of participants")

    application = await Application.create(
        project_id=data.project_id, applicant_id=current_user.id, cover_letter=data.cover_letter,
    )

    await log_activity(current_user.id, "apply", f"Applied to project '{project.title}'",
                       "application", application.id)

    owner = await User.filter(id=project.owner_id).first()
    if owner:
        bg.add_task(send_new_application_email, owner.email, owner.username, project.title, current_user.username)

    return application


@router.put("/{app_id}/status", response_model=ApplicationResponse)
async def update_status(app_id: int, data: ApplicationUpdateStatus, bg: BackgroundTasks,
                        current_user: User = Depends(get_current_user)):
    application = await Application.filter(id=app_id).first()
    if not application:
        raise HTTPException(status_code=404, detail="Application not found")

    project = await Project.filter(id=application.project_id).first()

    is_owner = project.owner_id == current_user.id
    is_applicant = application.applicant_id == current_user.id
    is_admin = current_user.role == RoleEnum.admin

    owner_statuses = {ApplicationStatus.accepted, ApplicationStatus.rejected,
                      ApplicationStatus.approved, ApplicationStatus.revision_requested, ApplicationStatus.completed}
    applicant_statuses = {ApplicationStatus.in_progress, ApplicationStatus.submitted}

    if data.status in owner_statuses and not (is_owner or is_admin):
        raise HTTPException(status_code=403, detail="Only project owner can perform this action")
    if data.status in applicant_statuses and not is_applicant:
        raise HTTPException(status_code=403, detail="Only applicant can perform this action")

    allowed = VALID_TRANSITIONS.get(application.status, [])
    if data.status not in allowed:
        raise HTTPException(
            status_code=400,
            detail=f"Cannot transition from {application.status.value} to {data.status.value}. "
                   f"Allowed: {[s.value for s in allowed]}"
        )

    application.status = data.status
    if data.status == ApplicationStatus.submitted and data.note:
        application.submission_note = data.note
    if data.status == ApplicationStatus.revision_requested and data.note:
        application.revision_note = data.note
    await application.save()

    await log_activity(current_user.id, "update_application_status",
                       f"Changed status to {data.status.value}", "application", app_id)

    applicant = await User.filter(id=application.applicant_id).first()
    if applicant:
        if data.status in owner_statuses:
            bg.add_task(send_application_status_email, applicant.email, applicant.username,
                        project.title, data.status.value)
        elif data.status == ApplicationStatus.submitted:
            owner = await User.filter(id=project.owner_id).first()
            if owner:
                bg.add_task(send_submission_email, owner.email, owner.username,
                            project.title, applicant.username)

    return application


@router.get("/project/{project_id}", response_model=list[ApplicationResponse])
async def get_project_applications(project_id: int,
                                   page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100),
                                   current_user: User = Depends(get_current_user)):
    project = await Project.filter(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")
    skip = (page - 1) * size
    return await Application.filter(project_id=project_id).offset(skip).limit(size)


@router.get("/my", response_model=list[ApplicationResponse])
async def get_my_applications(current_user: User = Depends(get_current_user)):
    return await Application.filter(applicant_id=current_user.id).order_by("-created_at")
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/applications/router.py
git commit -m "feat: rewrite applications router for Tortoise, move model to models.py"
```

---

### Task 10: Rewrite reviews router

**Files:**
- Rewrite: `backend/src/reviews/router.py`

- [ ] **Step 1: Rewrite `backend/src/reviews/router.py`**

Replace entire file with:

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException, BackgroundTasks, Query
from tortoise.functions import Avg, Count
from src.core.dependencies import get_current_user
from src.core.email import send_review_email
from src.users.models import User
from src.projects.models import Project
from src.applications.models import Application, ApplicationStatus
from src.reviews.models import Review
from src.notifications.router import create_notification


# -- Schemas --

class ReviewCreate(BaseModel):
    reviewee_id: int
    project_id: int
    application_id: Optional[int] = None
    rating: float = Field(..., ge=1.0, le=5.0)
    comment: Optional[str] = None


class ReviewResponse(BaseModel):
    id: int
    reviewer_id: int
    reviewee_id: int
    project_id: int
    application_id: Optional[int] = None
    rating: float
    comment: Optional[str] = None
    review_type: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


class UserRatingResponse(BaseModel):
    user_id: int
    average_rating: float
    total_reviews: int


# -- Router --

router = APIRouter(prefix="/reviews", tags=["Reviews"])


@router.post("/", response_model=ReviewResponse, status_code=201)
async def create_review(data: ReviewCreate, bg: BackgroundTasks,
                        current_user: User = Depends(get_current_user)):
    if current_user.id == data.reviewee_id:
        raise HTTPException(status_code=400, detail="Cannot review yourself")

    project = await Project.filter(id=data.project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    is_owner = project.owner_id == current_user.id
    review_type = "owner_to_student" if is_owner else "student_to_owner"

    existing = await Review.filter(
        reviewer_id=current_user.id, project_id=data.project_id, review_type=review_type
    ).first()
    if existing:
        raise HTTPException(status_code=400, detail="You already reviewed this user for this project")

    if data.application_id:
        app = await Application.filter(id=data.application_id).first()
        if not app or app.status not in (ApplicationStatus.approved, ApplicationStatus.completed):
            raise HTTPException(status_code=400, detail="Can only review after work is approved/completed")

    review = await Review.create(
        reviewer_id=current_user.id, reviewee_id=data.reviewee_id,
        project_id=data.project_id, application_id=data.application_id,
        rating=data.rating, comment=data.comment, review_type=review_type,
    )

    reviewee = await User.filter(id=data.reviewee_id).first()
    if reviewee:
        await create_notification(
            data.reviewee_id, "New Review",
            f"{current_user.username} left you a {data.rating}/5 review",
            notification_type="review", link=f"/profile/{data.reviewee_id}"
        )
        bg.add_task(send_review_email, reviewee.email, reviewee.username,
                    current_user.username, data.rating)

    return review


@router.get("/user/{user_id}", response_model=list[ReviewResponse])
async def get_user_reviews(user_id: int, page: int = Query(1, ge=1), size: int = Query(20, ge=1, le=100)):
    skip = (page - 1) * size
    return await Review.filter(reviewee_id=user_id).order_by("-created_at").offset(skip).limit(size)


@router.get("/user/{user_id}/rating", response_model=UserRatingResponse)
async def get_user_rating(user_id: int):
    result = await Review.filter(reviewee_id=user_id).annotate(
        avg_rating=Avg("rating"), total=Count("id")
    ).values("avg_rating", "total")
    if result:
        avg = result[0]["avg_rating"] or 0.0
        total = result[0]["total"] or 0
    else:
        avg, total = 0.0, 0
    return UserRatingResponse(user_id=user_id, average_rating=round(float(avg), 2), total_reviews=int(total))
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/reviews/router.py
git commit -m "feat: rewrite reviews router for Tortoise, move model to models.py"
```

---

### Task 11: Rewrite portfolio router

**Files:**
- Rewrite: `backend/src/portfolio/router.py`

- [ ] **Step 1: Rewrite `backend/src/portfolio/router.py`**

Replace entire file with:

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from fastapi import APIRouter, Depends, HTTPException
from src.core.dependencies import get_current_user
from src.users.models import User, StudentProfile, RoleEnum
from src.portfolio.models import PortfolioItem


# -- Schemas --

class PortfolioItemCreate(BaseModel):
    title: str = Field(..., min_length=3, max_length=255)
    description: Optional[str] = None
    project_url: Optional[str] = None
    image_url: Optional[str] = None


class PortfolioItemResponse(BaseModel):
    id: int
    student_id: int
    title: str
    description: Optional[str] = None
    project_url: Optional[str] = None
    image_url: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


# -- Router --

router = APIRouter(prefix="/portfolio", tags=["Portfolio"])


@router.post("/", response_model=PortfolioItemResponse, status_code=201)
async def add_item(data: PortfolioItemCreate, current_user: User = Depends(get_current_user)):
    if current_user.role != RoleEnum.student:
        raise HTTPException(status_code=403, detail="Only students have portfolios")
    student = await StudentProfile.filter(user_id=current_user.id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")

    item = await PortfolioItem.create(
        student_id=student.id, title=data.title, description=data.description,
        project_url=data.project_url, image_url=data.image_url,
    )
    return item


@router.get("/user/{user_id}", response_model=list[PortfolioItemResponse])
async def get_portfolio(user_id: int):
    student = await StudentProfile.filter(user_id=user_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student profile not found")
    return await PortfolioItem.filter(student_id=student.id).order_by("-created_at")


@router.delete("/{item_id}", status_code=204)
async def delete_item(item_id: int, current_user: User = Depends(get_current_user)):
    item = await PortfolioItem.filter(id=item_id).first()
    if not item:
        raise HTTPException(status_code=404, detail="Item not found")
    student = await StudentProfile.filter(user_id=current_user.id).first()
    if not student or item.student_id != student.id:
        raise HTTPException(status_code=403, detail="Not authorized")
    await item.delete()
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/portfolio/router.py
git commit -m "feat: rewrite portfolio router for Tortoise, move model to models.py"
```

---

### Task 12: Rewrite files router

**Files:**
- Modify: `backend/src/files/router.py`

- [ ] **Step 1: Rewrite `backend/src/files/router.py`**

Replace entire file with:

```python
import io
import os
import re
from datetime import datetime
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, UploadFile, File, HTTPException, Query
from fastapi.responses import StreamingResponse
from src.core.dependencies import get_current_user
from src.core.config import settings
from src.core.minio_client import upload_file, delete_file, download_file
from src.users.models import User, RoleEnum
from src.projects.models import Project, ProjectFile

ALLOWED_EXTENSIONS = {
    ".pdf", ".doc", ".docx", ".xls", ".xlsx", ".ppt", ".pptx",
    ".txt", ".csv", ".zip", ".rar", ".7z",
    ".png", ".jpg", ".jpeg", ".gif", ".svg",
    ".py", ".js", ".ts", ".java", ".cpp", ".c", ".go", ".rs",
    ".json", ".xml", ".yaml", ".yml", ".md",
}


def sanitize_filename(filename: str) -> str:
    filename = os.path.basename(filename)
    filename = re.sub(r'[^\w\s\-.]', '_', filename)
    filename = filename.strip('. ')
    return filename or "unnamed_file"


# -- Schemas --

class FileResponse(BaseModel):
    id: int
    project_id: int
    uploader_id: int
    filename: str
    object_name: str
    file_size: Optional[int] = None
    content_type: Optional[str] = None
    file_type: str
    download_url: Optional[str] = None
    created_at: datetime
    class Config:
        from_attributes = True


# -- Router --

router = APIRouter(prefix="/files", tags=["Files"])


@router.post("/project/{project_id}", response_model=FileResponse, status_code=201)
async def upload_project_file(
    project_id: int,
    file: UploadFile = File(...),
    file_type: str = Query("attachment", regex="^(attachment|submission)$"),
    current_user: User = Depends(get_current_user),
):
    project = await Project.filter(id=project_id).prefetch_related("applications").first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    is_owner = project.owner_id == current_user.id
    applications = await project.applications.all()
    is_applicant = any(a.applicant_id == current_user.id for a in applications)

    if file_type == "attachment" and not (is_owner or current_user.role == RoleEnum.admin):
        raise HTTPException(status_code=403, detail="Only project owner can upload attachments")
    if file_type == "submission" and not is_applicant:
        raise HTTPException(status_code=403, detail="Only applicants can upload submissions")

    safe_filename = sanitize_filename(file.filename or "unnamed_file")
    ext = os.path.splitext(safe_filename)[1].lower()
    if ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(status_code=400, detail=f"File type '{ext}' not allowed")

    content = await file.read()
    if len(content) > settings.MAX_FILE_SIZE:
        raise HTTPException(status_code=413, detail=f"File too large (max {settings.MAX_FILE_SIZE // 1024 // 1024}MB)")

    bucket = settings.MINIO_BUCKET_PROJECTS if file_type == "attachment" else settings.MINIO_BUCKET_SUBMISSIONS
    object_name = upload_file(bucket, content, safe_filename, file.content_type or "application/octet-stream")

    project_file = await ProjectFile.create(
        project_id=project_id, uploader_id=current_user.id,
        filename=safe_filename, object_name=object_name,
        file_size=len(content), content_type=file.content_type,
        file_type=file_type,
    )
    return project_file


@router.get("/project/{project_id}", response_model=list[FileResponse])
async def list_project_files(
    project_id: int,
    file_type: Optional[str] = None,
    current_user: User = Depends(get_current_user),
):
    filters = {"project_id": project_id}
    if file_type:
        filters["file_type"] = file_type
    files = await ProjectFile.filter(**filters).order_by("-created_at")

    response = []
    for f in files:
        data = FileResponse.model_validate(f)
        data.download_url = f"{settings.API_PREFIX}/files/{f.id}/download"
        response.append(data)
    return response


@router.get("/{file_id}/download")
async def download_project_file(file_id: int, current_user: User = Depends(get_current_user)):
    pf = await ProjectFile.filter(id=file_id).first()
    if not pf:
        raise HTTPException(status_code=404, detail="File not found")

    bucket = settings.MINIO_BUCKET_PROJECTS if pf.file_type == "attachment" else settings.MINIO_BUCKET_SUBMISSIONS
    try:
        file_data = download_file(bucket, pf.object_name)
    except Exception:
        raise HTTPException(status_code=404, detail="File not found in storage")

    content_type = pf.content_type or "application/octet-stream"
    return StreamingResponse(
        io.BytesIO(file_data),
        media_type=content_type,
        headers={"Content-Disposition": f'attachment; filename="{pf.filename}"'},
    )


@router.delete("/{file_id}", status_code=204)
async def delete_project_file(file_id: int, current_user: User = Depends(get_current_user)):
    pf = await ProjectFile.filter(id=file_id).first()
    if not pf:
        raise HTTPException(status_code=404, detail="File not found")
    if pf.uploader_id != current_user.id and current_user.role != RoleEnum.admin:
        raise HTTPException(status_code=403, detail="Not authorized")

    bucket = settings.MINIO_BUCKET_PROJECTS if pf.file_type == "attachment" else settings.MINIO_BUCKET_SUBMISSIONS
    delete_file(bucket, pf.object_name)
    await pf.delete()
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/files/router.py
git commit -m "feat: rewrite files router for Tortoise ORM"
```

---

### Task 13: Rewrite admin router

**Files:**
- Rewrite: `backend/src/admin/router.py`

- [ ] **Step 1: Rewrite `backend/src/admin/router.py`**

Replace entire file with:

```python
from typing import Optional
from pydantic import BaseModel
from fastapi import APIRouter, Depends, HTTPException, Query
from src.database.mongodb import get_mongodb
from src.core.dependencies import require_role
from src.core.redis import cache_get, cache_set
from src.users.models import User, RoleEnum
from src.users.schemas import UserResponse
from src.projects.models import Project, ProjectStatus
from src.applications.models import Application


# -- Schemas --

class AdminUserUpdate(BaseModel):
    is_active: Optional[bool] = None
    is_blocked: Optional[bool] = None
    role: Optional[RoleEnum] = None


class StatsResponse(BaseModel):
    total_users: int
    total_students: int
    total_companies: int
    total_projects: int
    total_applications: int
    active_projects: int
    total_chat_messages: int = 0
    total_notifications: int = 0


# -- Router --

router = APIRouter(prefix="/admin", tags=["Admin"])


@router.get("/stats", response_model=StatsResponse)
async def get_stats(current_user: User = Depends(require_role(RoleEnum.admin))):
    cached = await cache_get("admin:stats")
    if cached:
        return StatsResponse(**cached)

    mongo = await get_mongodb()
    chat_count = await mongo.chat_messages.count_documents({})
    notif_count = await mongo.notifications.count_documents({})

    stats = StatsResponse(
        total_users=await User.all().count(),
        total_students=await User.filter(role=RoleEnum.student).count(),
        total_companies=await User.filter(role=RoleEnum.company).count(),
        total_projects=await Project.all().count(),
        total_applications=await Application.all().count(),
        active_projects=await Project.filter(status=ProjectStatus.open).count(),
        total_chat_messages=chat_count,
        total_notifications=notif_count,
    )
    await cache_set("admin:stats", stats.model_dump(), ttl=60)
    return stats


@router.get("/users", response_model=list[UserResponse])
async def get_all_users(
    skip: int = Query(0, ge=0), limit: int = Query(20, ge=1, le=100),
    current_user: User = Depends(require_role(RoleEnum.admin)),
):
    return await User.all().offset(skip).limit(limit).prefetch_related("skills")


@router.put("/users/{user_id}", response_model=UserResponse)
async def update_user(
    user_id: int, data: AdminUserUpdate,
    current_user: User = Depends(require_role(RoleEnum.admin)),
):
    user = await User.filter(id=user_id).prefetch_related("skills").first()
    if not user:
        raise HTTPException(status_code=404, detail="User not found")
    await user.update_from_dict(data.model_dump(exclude_unset=True)).save()
    return user
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/admin/router.py
git commit -m "feat: rewrite admin router for Tortoise ORM"
```

---

### Task 14: Update chat router (remove SQLAlchemy imports)

**Files:**
- Modify: `backend/src/chat/router.py`

- [ ] **Step 1: Update imports in `backend/src/chat/router.py`**

Replace these imports at top of file:

```python
from sqlalchemy.ext.asyncio import AsyncSession
from src.database.postgres import get_db
from src.users.repository import UserRepository
```

with:

```python
from src.users.models import User as UserModel
```

Then update every occurrence of `UserRepository(db).get_by_id(...)` to `await UserModel.filter(id=...).first()`. Specifically:

In `create_or_get_room` (around line 104):

Replace:
```python
async def create_or_get_room(project_id: int, other_user_id: int,
                              db: AsyncSession = Depends(get_db),
                              current_user: User = Depends(get_current_user)):
    from src.projects.router import ProjectRepository
    project = await ProjectRepository(db).get_by_id(project_id)
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    user_repo = UserRepository(db)
    other = await user_repo.get_by_id(other_user_id)
```

with:

```python
async def create_or_get_room(project_id: int, other_user_id: int,
                              current_user: User = Depends(get_current_user)):
    from src.projects.models import Project
    project = await Project.filter(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")

    other = await UserModel.filter(id=other_user_id).first()
```

In `send_message_rest` (around line 169):

Replace:
```python
async def send_message_rest(room_id: str, data: SendMessageRequest, bg: BackgroundTasks,
                            db: AsyncSession = Depends(get_db),
                            current_user: User = Depends(get_current_user)):
```

with:

```python
async def send_message_rest(room_id: str, data: SendMessageRequest, bg: BackgroundTasks,
                            current_user: User = Depends(get_current_user)):
```

And replace (around line 206):
```python
        user_repo = UserRepository(db)
        other = await user_repo.get_by_id(uid)
```

with:

```python
        other = await UserModel.filter(id=uid).first()
```

Also remove the `User` import from `src.users.models` if it still imports it (it's imported as `User` in the schema typing via `get_current_user` — keep the import for the `User` type annotation in `get_current_user`). The cleanest approach: keep `from src.users.models import User` and remove the `UserModel` alias — just use `User` directly for queries too.

Final cleaned-up imports for `chat/router.py`:

```python
import json
import asyncio
import logging
from datetime import datetime, timezone
from typing import Optional
from pydantic import BaseModel
from bson import ObjectId
from fastapi import APIRouter, Depends, HTTPException, WebSocket, WebSocketDisconnect, Query, BackgroundTasks
from src.database.mongodb import get_mongodb
from src.core.dependencies import get_current_user
from src.core.security import decode_token
from src.core.redis import publish_message, get_redis
from src.core.email import send_chat_notification_email
from src.users.models import User
```

- [ ] **Step 2: Commit**

```bash
git add backend/src/chat/router.py
git commit -m "feat: remove SQLAlchemy imports from chat router"
```

---

### Task 15: Update main.py (lifespan and remove health endpoint)

**Files:**
- Rewrite: `backend/src/main.py`

- [ ] **Step 1: Rewrite `backend/src/main.py`**

Replace entire file with:

```python
import logging
from contextlib import asynccontextmanager
from fastapi import FastAPI
from fastapi.middleware.cors import CORSMiddleware

from src.core.config import settings
from src.database.postgres import init_postgres, close_postgres
from src.database.mongodb import init_mongodb, close_mongodb
from src.core.redis import close_redis
from src.core.minio_client import init_minio

from src.auth.router import router as auth_router
from src.users.router import router as users_router
from src.skills.router import router as skills_router
from src.projects.router import router as projects_router
from src.applications.router import router as applications_router
from src.files.router import router as files_router
from src.chat.router import router as chat_router
from src.notifications.router import router as notifications_router
from src.reviews.router import router as reviews_router
from src.portfolio.router import router as portfolio_router
from src.admin.router import router as admin_router

logging.basicConfig(level=logging.INFO, format="%(asctime)s [%(name)s] %(levelname)s: %(message)s")
logger = logging.getLogger(__name__)


@asynccontextmanager
async def lifespan(app: FastAPI):
    logger.info("Starting up...")
    await init_postgres()
    logger.info("PostgreSQL initialized (Tortoise ORM)")
    await init_mongodb()
    logger.info("MongoDB initialized")
    try:
        init_minio()
        logger.info("MinIO initialized")
    except Exception as e:
        logger.warning(f"MinIO init warning: {e}")
    yield
    await close_postgres()
    await close_mongodb()
    await close_redis()
    logger.info("Shutdown complete")


app = FastAPI(
    title=settings.PROJECT_NAME,
    version=settings.VERSION,
    description="Web platform for student-company-committee interaction. "
                "Features: projects, applications, chat, file uploads, reviews, notifications.",
    lifespan=lifespan,
    docs_url="/docs",
    redoc_url="/redoc",
)

app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.ALLOWED_ORIGINS,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "PATCH", "DELETE", "OPTIONS"],
    allow_headers=["Authorization", "Content-Type", "Accept"],
)

for r in [auth_router, users_router, skills_router, projects_router, applications_router,
          files_router, chat_router, notifications_router, reviews_router, portfolio_router, admin_router]:
    app.include_router(r, prefix=settings.API_PREFIX)


@app.get("/")
async def root():
    return {"message": settings.PROJECT_NAME, "version": settings.VERSION, "docs": "/docs"}
```

Key changes: `close_postgres()` replaces direct engine close, `/health` endpoint removed.

- [ ] **Step 2: Commit**

```bash
git add backend/src/main.py
git commit -m "feat: update main.py lifespan for Tortoise, remove health endpoint"
```

---

### Task 16: Rewrite test setup (conftest.py)

**Files:**
- Rewrite: `backend/src/tests/conftest.py`

- [ ] **Step 1: Rewrite `backend/src/tests/conftest.py`**

Replace entire file with:

```python
import pytest
import pytest_asyncio
from contextlib import ExitStack
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from tortoise import Tortoise

from src.main import app

TEST_MODELS = [
    "src.users.models",
    "src.skills.models",
    "src.projects.models",
    "src.applications.models",
    "src.reviews.models",
    "src.portfolio.models",
]


# Mock Redis
mock_redis_store = {}


async def mock_cache_get(key):
    return mock_redis_store.get(key)


async def mock_cache_set(key, value, ttl=None):
    mock_redis_store[key] = value


async def mock_cache_delete(key):
    mock_redis_store.pop(key, None)


async def mock_cache_delete_pattern(pattern):
    prefix = pattern.replace("*", "")
    keys = [k for k in mock_redis_store if k.startswith(prefix)]
    for k in keys:
        mock_redis_store.pop(k, None)


async def mock_blacklist(*a, **kw):
    pass


async def mock_is_blacklisted(token):
    return False


async def mock_incr_counter(key):
    return 1


async def mock_get_counter(key):
    return 0


async def mock_reset_counter(key):
    pass


async def mock_publish_message(channel, data):
    pass


async def mock_rate_limit_check(key, max_requests=5, window=60):
    return True


# Mock MongoDB
class MockCollection:
    def __init__(self):
        self.docs = []
        self._counter = 0

    async def insert_one(self, doc):
        self._counter += 1
        from bson import ObjectId
        doc["_id"] = ObjectId()
        self.docs.append(doc)
        return MagicMock(inserted_id=doc["_id"])

    async def find_one(self, *a, **kw):
        return self.docs[0] if self.docs else None

    async def find_one_and_update(self, *a, **kw):
        return self.docs[0] if self.docs else None

    async def update_one(self, *a, **kw):
        pass

    async def update_many(self, *a, **kw):
        pass

    async def count_documents(self, query):
        return len(self.docs)

    def find(self, *a, **kw):
        return MockCursor(self.docs)

    async def create_index(self, *a, **kw):
        pass


class MockCursor:
    def __init__(self, docs):
        self._docs = docs
        self._skip = 0
        self._limit = 100

    def sort(self, *a, **kw):
        return self

    def skip(self, n):
        self._skip = n
        return self

    def limit(self, n):
        self._limit = n
        return self

    def __aiter__(self):
        self._iter = iter(self._docs[self._skip:self._skip + self._limit])
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class MockMongoDB:
    def __init__(self):
        self.chat_messages = MockCollection()
        self.chat_rooms = MockCollection()
        self.notifications = MockCollection()
        self.activity_logs = MockCollection()


mock_mongo = MockMongoDB()


async def mock_get_mongodb():
    return mock_mongo


async def mock_init_mongodb():
    pass


# Apply all patches
PATCHES = [
    # Redis core
    ("src.core.redis.cache_get", mock_cache_get),
    ("src.core.redis.cache_set", mock_cache_set),
    ("src.core.redis.cache_delete", mock_cache_delete),
    ("src.core.redis.cache_delete_pattern", mock_cache_delete_pattern),
    ("src.core.redis.blacklist_token", mock_blacklist),
    ("src.core.redis.is_token_blacklisted", mock_is_blacklisted),
    ("src.core.redis.incr_counter", mock_incr_counter),
    ("src.core.redis.get_counter", mock_get_counter),
    ("src.core.redis.reset_counter", mock_reset_counter),
    ("src.core.redis.publish_message", mock_publish_message),
    # Redis at import sites
    ("src.auth.router.rate_limit_check", mock_rate_limit_check),
    ("src.auth.router.cache_set", mock_cache_set),
    ("src.auth.router.cache_get", mock_cache_get),
    ("src.auth.router.cache_delete", mock_cache_delete),
    ("src.core.dependencies.is_token_blacklisted", mock_is_blacklisted),
    ("src.users.service.cache_get", mock_cache_get),
    ("src.users.service.cache_set", mock_cache_set),
    ("src.users.service.cache_delete", mock_cache_delete),
    ("src.skills.router.cache_get", mock_cache_get),
    ("src.skills.router.cache_set", mock_cache_set),
    ("src.skills.router.cache_delete", mock_cache_delete),
    ("src.projects.router.cache_delete_pattern", mock_cache_delete_pattern),
    ("src.admin.router.cache_get", mock_cache_get),
    ("src.admin.router.cache_set", mock_cache_set),
    ("src.chat.router.publish_message", mock_publish_message),
    # MongoDB
    ("src.database.mongodb.get_mongodb", mock_get_mongodb),
    ("src.database.mongodb.init_mongodb", mock_init_mongodb),
    ("src.notifications.router.get_mongodb", mock_get_mongodb),
    ("src.chat.router.get_mongodb", mock_get_mongodb),
    ("src.admin.router.get_mongodb", mock_get_mongodb),
    # Notification counters
    ("src.notifications.router.incr_counter", mock_incr_counter),
    ("src.notifications.router.get_counter", mock_get_counter),
    ("src.notifications.router.reset_counter", mock_reset_counter),
    # Chat Redis
    ("src.chat.router.get_redis", AsyncMock(return_value=MagicMock(pubsub=MagicMock(return_value=MagicMock(
        subscribe=AsyncMock(), unsubscribe=AsyncMock(), close=AsyncMock(),
        listen=MagicMock(return_value=AsyncMock().__aiter__()),
    ))))),
    # Activity logging
    ("src.core.activity.get_mongodb", mock_get_mongodb),
    ("src.auth.service.log_activity", AsyncMock()),
    ("src.applications.router.log_activity", AsyncMock()),
    # Email
    ("src.core.email._send_smtp", AsyncMock()),
]


@pytest.fixture(autouse=True)
def patch_externals():
    with ExitStack() as stack:
        for target, mock_obj in PATCHES:
            stack.enter_context(patch(target, mock_obj))
        mock_redis_store.clear()
        mock_mongo.chat_messages = MockCollection()
        mock_mongo.chat_rooms = MockCollection()
        mock_mongo.notifications = MockCollection()
        mock_mongo.activity_logs = MockCollection()
        yield


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": TEST_MODELS},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _register_and_verify(client: AsyncClient, email: str, username: str, password: str, role: str) -> str:
    """Register a user, verify their email, and return an access token."""
    existing_keys = {k for k in mock_redis_store if k.startswith("email_verify:")}
    await client.post("/api/v1/auth/register", json={
        "email": email, "username": username, "password": password, "role": role
    })
    new_keys = {k for k in mock_redis_store if k.startswith("email_verify:")} - existing_keys
    for key in new_keys:
        verify_token = key.split(":", 1)[1]
        await client.get(f"/api/v1/auth/verify-email?token={verify_token}")
    resp = await client.post("/api/v1/auth/login", data={"username": username, "password": password})
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def student_token(client: AsyncClient):
    return await _register_and_verify(client, "s@test.com", "student1", "pass123", "student")


@pytest_asyncio.fixture
async def company_token(client: AsyncClient):
    return await _register_and_verify(client, "c@test.com", "company1", "pass123", "company")


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient):
    return await _register_and_verify(client, "a@test.com", "admin1", "pass123", "admin")


def auth(token: str):
    return {"Authorization": f"Bearer {token}"}
```

Key changes:
- Removed all SQLAlchemy imports (engine, session, Base, get_db, StaticPool, aiosqlite)
- Removed `app.dependency_overrides[get_db]` (no more get_db dependency)
- `setup_db` uses `Tortoise.init()` with `sqlite://:memory:` and `Tortoise.generate_schemas()`
- Removed patches for `src.projects.router.cache_get` and `src.projects.router.cache_set` (projects router no longer uses cache_get/cache_set — only cache_delete_pattern)
- Removed `src.auth.service.blacklist_token` patch (blacklist_token is now imported from src.core.redis, patched at core level)

- [ ] **Step 2: Run tests to verify**

Run: `cd backend && python -m pytest src/tests/ -v`
Expected: All 50 tests pass.

Note: some tests may need minor adjustments if Tortoise serializes fields differently from SQLAlchemy. Address any failures case-by-case in Step 3.

- [ ] **Step 3: Fix any test failures**

If tests fail due to Tortoise ORM differences (e.g., Pydantic serialization of Tortoise models, field access patterns), fix them. Common issues:
- Tortoise ForeignKey fields store `_id` suffix by default (e.g., `project_id` is accessed as `project_id` on the model)
- `from_attributes = True` in Pydantic schemas should work with Tortoise models
- M2M fields need `prefetch_related` before access

- [ ] **Step 4: Commit**

```bash
git add backend/src/tests/conftest.py
git commit -m "feat: rewrite test setup for Tortoise ORM with in-memory SQLite"
```

---

### Task 17: Delete Alembic and set up Aerich

**Files:**
- Delete: `backend/alembic/` (entire directory)
- Delete: `backend/alembic.ini`

- [ ] **Step 1: Delete Alembic files**

```bash
rm -rf backend/alembic backend/alembic.ini
```

- [ ] **Step 2: Initialize Aerich**

```bash
cd backend
aerich init -t src.database.postgres.TORTOISE_ORM
aerich init-db
```

This creates a `migrations/` directory with the initial schema migration.

- [ ] **Step 3: Commit**

```bash
git rm -r backend/alembic backend/alembic.ini
git add backend/migrations/ backend/pyproject.toml
git commit -m "feat: replace Alembic with Aerich for Tortoise ORM migrations"
```

---

### Task 18: Update schemas for Tortoise compatibility

**Files:**
- Modify: `backend/src/users/schemas.py`

- [ ] **Step 1: Update Pydantic schemas**

Tortoise models work with `from_attributes = True` but some schemas may need `model_config` instead of inner `Config` class for Pydantic v2. The current schemas use `class Config: from_attributes = True` which is valid in Pydantic v2 (legacy style). No change needed unless tests reveal issues.

However, verify that `UserResponse` correctly serializes the `skills` M2M field. Tortoise M2M fields return a `ManyToManyRelation` object — Pydantic needs the field to be pre-fetched (`prefetch_related("skills")`) before serialization. This is already done in `get_current_user` and all router endpoints.

- [ ] **Step 2: Run full test suite**

Run: `cd backend && python -m pytest src/tests/ -v --cov=src --cov-report=term-missing`
Expected: All tests pass with ~80% coverage.

- [ ] **Step 3: Commit any fixes**

```bash
git add -A
git commit -m "fix: adjust schemas for Tortoise ORM compatibility"
```

---

### Task 19: Update CLAUDE.md and .env

**Files:**
- Modify: `CLAUDE.md`
- Modify: `backend/.env`

- [ ] **Step 1: Update CLAUDE.md**

Replace all SQLAlchemy references with Tortoise ORM:
- Change "SQLAlchemy 2.0 async via asyncpg" to "Tortoise ORM async via asyncpg"
- Change "Alembic" references to "Aerich"
- Update migration commands to `aerich migrate` / `aerich upgrade`
- Remove repository layer references
- Note that `get_db` dependency no longer exists
- Update test description to mention Tortoise's built-in SQLite test support

- [ ] **Step 2: Commit**

```bash
git add CLAUDE.md
git commit -m "docs: update CLAUDE.md for Tortoise ORM migration"
```

---

### Task 20: Final verification

- [ ] **Step 1: Run full test suite**

```bash
cd backend && python -m pytest src/tests/ -v --cov=src --cov-report=term-missing
```

Expected: All 50 tests pass.

- [ ] **Step 2: Start Docker services and smoke test**

```bash
docker compose up --build -d
```

Wait for services to start, then:

```bash
curl http://localhost:8000/
curl http://localhost:8000/docs
```

Expected: Root returns JSON with project name/version. Swagger UI loads.

- [ ] **Step 3: Test basic auth flow**

```bash
# Register
curl -X POST http://localhost:8000/api/v1/auth/register \
  -H "Content-Type: application/json" \
  -d '{"email":"test@test.com","username":"testuser","password":"pass123","role":"student"}'

# Login (after email verification or set is_active=True manually)
curl -X POST http://localhost:8000/api/v1/auth/login \
  -d "username=testuser&password=pass123"
```

- [ ] **Step 4: Final commit if any fixes**

```bash
git add -A
git commit -m "fix: final adjustments after Tortoise ORM migration"
```
