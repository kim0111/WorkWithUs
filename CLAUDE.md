# CLAUDE.md

This file provides guidance to Claude Code (claude.ai/code) when working with code in this repository.

## Project Overview

NexusHub Platform v2.0 — a web platform for student-company-committee interaction. Students apply to company projects, work on them through an 8-stage workflow, and exchange reviews. Features include real-time chat (WebSocket), file uploads, notifications, and admin tools.

## Commands

### Run all services (Docker)
```bash
docker compose up --build
```
- API: http://localhost:8000 | Swagger: http://localhost:8000/docs
- Frontend: http://localhost:3000
- MinIO Console: http://localhost:9001

### Backend tests (68 tests)
```bash
# Locally (requires Python 3.11+)
cd backend
pip install -r requirements.txt
pytest src/tests/ -v

# Single test file
pytest src/tests/test_auth.py -v

# Single test
pytest src/tests/test_auth.py::test_register_student -v
```

### Database migrations (Aerich, run from `backend/`)
```bash
# Initialize (first time only)
aerich init -t src.database.postgres.TORTOISE_ORM
aerich init-db

# Create and apply migrations
aerich migrate --name "description"
aerich upgrade
```

### Frontend dev server
```bash
cd frontend
npm install
npm run dev        # Vite dev server on :3000, proxies /api to backend:8000
npm run build      # Production build
```

## Architecture

**Backend:** FastAPI (async) with domain-based module structure. Each domain (`auth/`, `users/`, `projects/`, etc.) under `backend/src/` has its own router, schemas, and models files. Services exist for `auth` and `users` (business logic beyond CRUD). All routers are mounted at `/api/v1` prefix in `src/main.py`.

**Frontend:** Vue 3 SPA with Composition API, Pinia stores, Vue Router with auth/guest/admin guards. Axios instance in `src/api/index.js` handles JWT token injection and automatic refresh on 401.

### Four-database architecture
| Database | Purpose | Access layer |
|----------|---------|-------------|
| **PostgreSQL 16** | Relational data (users, projects, applications, reviews, portfolio, file metadata) | Tortoise ORM async via `asyncpg` |
| **MongoDB 7** | Documents with high write throughput (chat messages/rooms, notifications, activity logs) | Motor async driver |
| **Redis 7** | JWT blacklist, caching (skills, stats, profiles), pub/sub for chat, notification counters, rate limiting | `redis` async client |
| **MinIO** | S3-compatible file storage. Buckets: `avatars`, `project-files`, `submissions`, `resumes` | `minio` Python SDK |

### Key patterns
- **Tortoise ORM** — models use `tortoise.models.Model`, queries via QuerySet API (`Model.filter()`, `Model.create()`, etc.). No repository layer — routers/services query Tortoise directly
- **No `get_db` dependency** — Tortoise manages connections globally via `Tortoise.init()` in the FastAPI lifespan. No session injection needed
- **Async throughout** — all DB access, email (aiosmtplib), file operations are async/await
- **Dependency injection** via FastAPI's `Depends()` — `get_current_user`, `require_role`
- **User roles:** `student`, `company`, `committee`, `admin` — enforced by `require_role()` in `src/core/dependencies.py`
- **Application workflow:** `pending -> accepted -> in_progress -> submitted -> approved -> completed` (with `rejected` and `revision_requested` branches). Every transition must call `_append_history(...)` in `applications/router.py` — the per-row `status_history` JSONField is the audit log consumed by the frontend `ApplicationTimeline`. Scripts that patch only history must use `save(update_fields=["status_history"])` to avoid bumping `updated_at`.
- **JWT auth:** access tokens (30min) + refresh tokens (7 days), blacklist on logout via Redis
- **Settings:** `src/core/config.py` uses Pydantic `BaseSettings` with `.env` file. `SECRET_KEY` has no default and must be set. `DATABASE_URL` uses Tortoise format: `asyncpg://...`

### Frontend patterns
- **Pinia stores** in `frontend/src/stores/`: `auth`, `projects`, `notifications`, `applications`. New code should consume these instead of calling `src/api/` directly. The `applications` store patches state in place (`myApps`, `byProject`), so a status change in one view (e.g., `ApplicationDetailDrawer`) is immediately visible in all other views reading the same store.
- **Shared component library** in `frontend/src/components/`: `BaseModal`, `BaseTabs`, `StatusBadge`, `EmptyState`, `FormField`, `ConfirmDialog`, `SkillPicker`, `SkeletonBlock`, `ApplicationTimeline`, `ApplicationDetailDrawer`. Reuse before creating new primitives.
- **Role-based orchestrators** — `DashboardPage` and `ProfilePage` are thin shells that dispatch to role-specific sub-components under `components/dashboard/` and `components/profile/`. Extend by adding or editing a sub-component, not by branching inside the orchestrator.
- **Route guards** — `frontend/src/router/` enforces `requiresAuth`, `requiresGuest`, `requiresAdmin`, and role whitelists; a catch-all route renders `NotFoundPage` with the navbar hidden.

### Testing approach
Tests use in-memory SQLite (via `aiosqlite`) with `Tortoise.init(db_url="sqlite://:memory:")`. Redis, MongoDB, MinIO, and SMTP are all mocked via `unittest.mock.patch` defined in `src/tests/conftest.py`. The `conftest.py` `PATCHES` list is the central place where all external service mocks are wired. When adding new Redis/MongoDB calls in routers, the corresponding mock must be added to `PATCHES` for both the core module path and the import-site path.

### Email (SMTP)
Async email via `aiosmtplib` in `src/core/email.py`. Defaults to Gmail SMTP (`smtp.gmail.com:587` with TLS). Requires `SMTP_USER` and `SMTP_PASSWORD` in `backend/.env` — without them, emails are logged but not sent. Seven email types: verification, welcome, application status, new application, submission, chat notification, review. All dispatched via FastAPI `BackgroundTasks`.

### Port mapping
Docker Compose maps PostgreSQL to host port **5435** (not 5432) to avoid conflicts with local PostgreSQL. All other services use standard ports.
