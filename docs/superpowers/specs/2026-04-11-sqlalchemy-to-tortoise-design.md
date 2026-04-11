# SQLAlchemy to Tortoise ORM Migration — Design Spec

## Goal

Replace SQLAlchemy with Tortoise ORM across the entire backend for:
- Simpler, more Django-like model definitions with less boilerplate
- Better async-native experience (Tortoise is async-first)
- Easier migrations via Aerich (replaces Alembic)

## Approach

Bottom-up migration in dependency order: models → database setup → dependencies → services/routers → tests → migrations. The app will be non-functional mid-migration but the codebase is small (~20 files) so the broken window is short.

## Section 1: Models & Database Setup

### Tortoise Initialization

Replace `database/postgres.py` (engine, sessionmaker, Base, get_db, init_postgres) with Tortoise.init() called in the FastAPI lifespan:

```python
await Tortoise.init(
    db_url="asyncpg://postgres:postgres@postgres:5432/platform_db",
    modules={"models": [
        "src.users.models", "src.skills.models", "src.projects.models",
        "src.applications.models", "src.reviews.models", "src.portfolio.models"
    ]}
)
await Tortoise.generate_schemas()
```

No more `get_db` dependency — Tortoise manages connections globally.

### Model File Structure

Every domain gets its own `models.py` (fixing current inconsistency where Application, Review, PortfolioItem live in router files):

```
src/
├── users/models.py        — User, CompanyProfile, StudentProfile
├── skills/models.py       — Skill
├── projects/models.py     — Project, ProjectFile
├── applications/models.py — Application  (NEW file, moved from router.py)
├── reviews/models.py      — Review       (NEW file, moved from router.py)
├── portfolio/models.py    — PortfolioItem (NEW file, moved from router.py)
```

### Model Translation Rules

| SQLAlchemy | Tortoise |
|---|---|
| `class User(Base)` | `class User(Model)` |
| `Column(Integer, primary_key=True)` | `fields.IntField(pk=True)` |
| `Column(String(255), unique=True)` | `fields.CharField(max_length=255, unique=True)` |
| `Column(Text)` | `fields.TextField()` |
| `Column(Float)` | `fields.FloatField()` |
| `Column(Boolean, default=True)` | `fields.BooleanField(default=True)` |
| `Column(DateTime, default=func.now())` | `fields.DatetimeField(auto_now_add=True)` |
| `Column(Enum(...))` | `fields.CharEnumField(enum_type=MyEnum)` |
| `ForeignKey("users.id")` + `relationship()` | `fields.ForeignKeyField("models.User", related_name="...")` |
| `relationship("Skill", secondary=user_skills)` + association table | `fields.ManyToManyField("models.Skill", related_name="users")` |
| `UniqueConstraint("project_id", "applicant_id")` | `class Meta: unique_together = (("project", "applicant"),)` |
| `__tablename__ = "users"` | `class Meta: table = "users"` |

### Enum Definitions

Enums stay as Python enums but referenced via `CharEnumField`:
- `UserRole`: student, company, committee, admin
- `ProjectStatus`: open, in_progress, closed
- `ApplicationStatus`: pending, accepted, rejected, in_progress, submitted, revision_requested, approved, completed
- `FileType`: attachment, submission
- `ReviewType`: owner_to_student, student_to_owner

## Section 2: Removing the Repository Layer

### Current Architecture (3 layers)

```
Router → Service → Repository → SQLAlchemy session → DB
```

### New Architecture (2 layers)

```
Router → Service → Tortoise QuerySet → DB
```

### What Gets Removed

- `src/users/repository.py` — deleted (UserRepository, CompanyProfileRepository, StudentProfileRepository)
- Repository classes embedded in `projects/router.py`, `applications/router.py`, `reviews/router.py`, `skills/router.py` — absorbed into services or routers

### Query Translation

```python
# SQLAlchemy: get by ID with eager loading
result = await db.execute(select(User).options(selectinload(User.skills)).where(User.id == user_id))
user = result.scalar_one_or_none()

# Tortoise
user = await User.filter(id=user_id).prefetch_related("skills").first()
```

```python
# SQLAlchemy: M2M add
await db.execute(user_skills.insert().values(user_id=uid, skill_id=sid))

# Tortoise
await user.skills.add(skill)
```

```python
# SQLAlchemy: aggregation
result = await db.execute(select(func.avg(Review.rating)).where(Review.reviewee_id == uid))

# Tortoise
result = await Review.filter(reviewee_id=uid).aggregate(avg_rating=Avg("rating"))
```

```python
# SQLAlchemy: count
result = await db.execute(select(func.count(User.id)).where(User.role == role))

# Tortoise
count = await User.filter(role=role).count()
```

```python
# SQLAlchemy: CRUD
db.add(obj); await db.flush(); await db.refresh(obj)  # create
setattr(obj, field, value); await db.flush()            # update
await db.delete(obj)                                    # delete

# Tortoise
obj = await Model.create(**data)           # create
obj.field = value; await obj.save()        # update
await obj.delete()                         # delete
```

### Dependency Injection Changes

- `db: AsyncSession = Depends(get_db)` removed from all router signatures
- `get_current_user` in `core/dependencies.py` queries Tortoise directly (no db parameter)
- `require_role()` unchanged (wraps get_current_user)
- Services drop `self.db` / `self.repo` attributes, call Tortoise QuerySet directly

### Services That Stay

- `auth/service.py` — registration, login, token logic (has business logic beyond CRUD)
- `users/service.py` — profile updates, skill management, cache invalidation

## Section 3: Router Updates

### Changes Applied to Every Router

- Remove `db: AsyncSession = Depends(get_db)` from endpoint signatures
- Remove repository instantiation
- Replace SQLAlchemy queries with Tortoise QuerySet calls
- `db.add()`/`flush()`/`refresh()` → `Model.create()`
- `db.execute(select(...))` → Tortoise filter/get/all
- `db.delete()` → `obj.delete()`

### Dynamic Filter Building (projects router)

```python
# Current
query = select(Project).options(selectinload(Project.required_skills))
if status:
    query = query.where(Project.status == status)
if search:
    query = query.where(Project.title.ilike(f"%{search}%"))

# New
query = Project.all().prefetch_related("required_skills")
if status:
    query = query.filter(status=status)
if search:
    query = query.filter(title__icontains=search)
```

### Removals

- `/health` endpoint removed from `main.py` (Docker Compose healthchecks are sufficient)
- `chat/router.py` SQLAlchemy import removed (uses MongoDB only)

## Section 4: Aerich Migrations & Test Setup

### Replace Alembic with Aerich

Delete: `alembic/` directory, `alembic.ini`

Aerich config embedded in Tortoise config:

```python
TORTOISE_ORM = {
    "connections": {"default": settings.DATABASE_URL},
    "apps": {
        "models": {
            "models": [
                "src.users.models", "src.skills.models", "src.projects.models",
                "src.applications.models", "src.reviews.models", "src.portfolio.models",
                "aerich.models"
            ],
            "default_connection": "default",
        }
    }
}
```

Commands: `aerich init -t src.core.config.TORTOISE_ORM`, `aerich init-db`, `aerich migrate`, `aerich upgrade`

### Test Setup Rewrite

Replace SQLAlchemy in-memory SQLite with Tortoise test utilities:

```python
from tortoise.contrib.test import initializer, finalizer

@pytest.fixture(autouse=True)
async def init_db():
    initializer(
        ["src.users.models", "src.skills.models", "src.projects.models",
         "src.applications.models", "src.reviews.models", "src.portfolio.models"],
        db_url="sqlite://:memory:"
    )
    yield
    finalizer()
```

- `get_db` override deleted (no dependency to override)
- All Redis/MongoDB/MinIO/SMTP mock patches unchanged
- `aiosqlite` removed from requirements (Tortoise bundles its own SQLite support)

### requirements.txt Changes

```diff
- sqlalchemy[asyncio]==2.0.36
- asyncpg==0.30.0
- alembic==1.14.1
- aiosqlite==0.20.0
+ tortoise-orm[asyncpg]==0.25.1
+ aerich==0.8.2
```

## Files Changed Summary

### Deleted
- `src/users/repository.py`
- `alembic/` (entire directory)
- `alembic.ini`

### Created
- `src/applications/models.py` (Application model, moved from router.py)
- `src/reviews/models.py` (Review model, moved from router.py)
- `src/portfolio/models.py` (PortfolioItem model, moved from router.py)
- `migrations/` (Aerich-generated)

### Modified
- `src/database/postgres.py` — rewritten (Tortoise init/close)
- `src/core/config.py` — add TORTOISE_ORM dict, change DATABASE_URL format
- `src/core/dependencies.py` — remove get_db usage, query Tortoise directly
- `src/main.py` — new lifespan with Tortoise.init(), remove /health endpoint
- `src/users/models.py` — rewrite to Tortoise models
- `src/skills/models.py` — rewrite to Tortoise models
- `src/projects/models.py` — rewrite to Tortoise models
- `src/auth/service.py` — remove repository usage, use Tortoise QuerySet
- `src/auth/router.py` — remove db dependency
- `src/users/service.py` — remove repository usage, use Tortoise QuerySet
- `src/users/router.py` — remove db dependency, remove repo instantiation
- `src/skills/router.py` — remove embedded repo, use Tortoise QuerySet
- `src/projects/router.py` — remove embedded repo/service, use Tortoise QuerySet
- `src/applications/router.py` — move model out, remove repo, use Tortoise QuerySet
- `src/reviews/router.py` — move model out, remove repo, use Tortoise QuerySet
- `src/portfolio/router.py` — move model out, use Tortoise QuerySet
- `src/files/router.py` — remove db dependency, use Tortoise QuerySet
- `src/admin/router.py` — remove db/repo usage, use Tortoise QuerySet
- `src/chat/router.py` — remove SQLAlchemy import
- `src/tests/conftest.py` — rewrite DB setup for Tortoise
- `requirements.txt` — swap dependencies

## Not Changing

- MongoDB layer (Motor) — untouched
- Redis layer — untouched
- MinIO layer — untouched
- Email (aiosmtplib) — untouched
- Pydantic schemas — untouched
- All Redis/MongoDB/MinIO/SMTP test mocks — untouched
- Frontend — untouched
- Auth logic (JWT, bcrypt) — same logic, different DB access
- Docker Compose / Dockerfiles — untouched
