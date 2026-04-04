# Backend Issues Tracker

## Critical

| # | Issue | Location | Status |
|---|-------|----------|--------|
| 1 | **Hardcoded secrets in docker-compose.yml** — JWT secret, DB passwords, MinIO creds in plaintext in version control | `docker-compose.yml` | ✅ |
| 2 | **Hardcoded secret defaults in config.py** — `SECRET_KEY = "super-secret-key-change-in-production"` as default | `core/config.py` | ✅ |
| 3 | **Broken cache logic in UserService** — cache is checked but DB is fetched anyway, cache never actually used | `users/service.py` | ✅ |
| 4 | **No rate limiting on login** — brute-force attacks possible on `/auth/login` | `auth/router.py` | ✅ |
| 5 | **No file upload validation** — no file type/extension whitelist, filename used directly (path traversal risk) | `files/router.py` | ✅ |
| 6 | **No transactions for multi-step operations** — User + Profile creation is non-atomic; partial failure leaves orphaned records | `auth/service.py` | ✅ |
| 7 | **Dockerfile runs `--reload` and as root** — reload flag in production is a security risk, no non-root user | `Dockerfile` | ✅ |
| 8 | **Race condition on duplicate application check** — check-then-insert is non-atomic, no DB unique constraint | `applications/router.py` | ✅ |

## Medium

| # | Issue | Location | Status |
|---|-------|----------|--------|
| 9 | **No email verification on registration** — any email (even fake) can register | `auth/router.py` | ✅ |
| 10 | **Missing auth on file listing endpoint** — anyone can list project files by ID | `files/router.py` | ✅ |
| 11 | **WebSocket token in query param** — tokens logged in browser history/server logs | `chat/router.py` | ✅ |
| 12 | **CORS too permissive** — `allow_methods=["*"]` instead of explicit list | `main.py` | ✅ |
| 13 | **Synchronous SMTP blocks event loop** — `smtplib.SMTP()` in BackgroundTasks | `core/email.py` | ✅ |
| 14 | **`max_participants` never enforced** — model field exists but applications exceed the limit | `projects/models.py`, `applications/router.py` | ✅ |
| 15 | **Health check is fake** — returns hardcoded "connected" without actually checking services | `main.py` | ✅ |
| 16 | **No pagination on several list endpoints** — `get_project_applications`, `get_user_reviews` return all rows | `applications/router.py`, `reviews/router.py` | ✅ |
| 17 | **Inconsistent repository pattern** — Users has clean `repository.py`, others define repos inline in routers | across modules | ⬜ |
| 18 | **Test DB uses file-based SQLite** — `sqlite:///./test.db` persists between runs, not isolated | `tests/conftest.py` | ✅ |
| 19 | **No activity logging** — MongoDB `activity_logs` collection exists but is never written to | entire backend | ✅ |
| 20 | **Missing student/company profile endpoints** — models exist but no dedicated CRUD routes | `users/router.py` | ✅ |

## Low

| # | Issue | Location | Status |
|---|-------|----------|--------|
| 21 | **No soft deletes** — all deletes are permanent, no recovery possible | across modules | ⬜ |
| 22 | **No structured logging** — basic `logging.info` only, no JSON/structured format for monitoring | `main.py` | ⬜ |
| 23 | **Missing type hints** on many async functions | across modules | ⬜ |
| 24 | **No search users by skill** — skills relationship exists but no search endpoint | `users/router.py` | ⬜ |
| 25 | **No resume upload endpoint** — `StudentProfile.resume_url` field exists but no upload route | `users/`, `files/` | ⬜ |
| 26 | **N+1 query risk** — eager loads skills + attachments on every project list query | `projects/router.py` | ⬜ |
| 27 | **No request/response logging middleware** — no audit trail of API calls | `main.py` | ⬜ |
| 28 | **MongoDB no connection pool config** — default pool params, could exhaust under load | `database/mongodb.py` | ⬜ |
| 29 | **Missing ObjectId validation** — invalid MongoDB IDs cause 500 instead of 400 | `chat/router.py`, `notifications/router.py` | ⬜ |
| 30 | **Broad exception catching** in file download with no logging | `files/router.py` | ⬜ |
