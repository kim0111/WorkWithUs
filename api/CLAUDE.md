# WorkWithUs API

## Stack
FastAPI + Tortoise ORM + PostgreSQL, modular monolith.

## Project Structure
```
src/
├── main.py          # FastAPI app, lifespan, router registration
├── config.py        # Settings (pydantic-settings, reads .env)
├── auth/            # JWT auth: register, login, refresh, logout
│   ├── router.py
│   ├── service.py   # password hashing, JWT creation/decode, blacklist
│   ├── schemas.py
│   └── dependencies.py  # get_current_user, require_role()
├── users/           # User profiles (student/company)
│   ├── router.py
│   ├── service.py
│   ├── models.py    # User, StudentProfile, CompanyProfile
│   └── schemas.py
└── skills/          # Skills for matching
    ├── router.py
    ├── service.py
    ├── models.py    # Skill + M2M with StudentProfile
    └── schemas.py
```

## Architecture Pattern
Router → Service (→ Model directly via Tortoise ORM).
Each module has: models.py, schemas.py, service.py, router.py.

## Commands
```bash
uv run uvicorn src.main:app --reload    # dev server
uv run aerich upgrade                    # run migrations
uv run aerich migrate --name <name>      # create migration
```

## API Prefix: `/api/v1`

## Conventions
- All models use Tortoise ORM (not SQLAlchemy)
- Pydantic v2 schemas for request/response
- UUIDs for user-facing PKs, int PKs for reference data (skills)
- Auth via Bearer JWT (access 15min + refresh 7d)
- Admin role cannot be self-registered
- Token blacklist is in-memory (will move to Redis later)
