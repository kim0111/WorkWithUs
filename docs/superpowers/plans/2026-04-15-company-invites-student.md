# Company Invites Student Implementation Plan

> **For agentic workers:** REQUIRED SUB-SKILL: Use superpowers:subagent-driven-development (recommended) or superpowers:executing-plans to implement this plan task-by-task. Steps use checkbox (`- [ ]`) syntax for tracking.

**Goal:** Let companies search students and directly invite them to projects, with the student accepting or declining.

**Architecture:** Extend the existing `applications` table with an `invited` status and an `initiator` column. Invites flow through the same state machine — on acceptance they become `accepted` and enter the existing workflow. Search is a new read-only endpoint over `users + user_skills + student_profiles` with a derived-availability subquery.

**Tech Stack:** FastAPI + Tortoise ORM (PostgreSQL), Aerich migrations, MongoDB for notifications, Redis for cache. Vue 3 + Pinia + Vue Router on the frontend.

**Spec:** `docs/superpowers/specs/2026-04-15-company-invites-student-design.md`

---

## File Structure

### Backend

| File | Role |
|------|------|
| `backend/src/applications/models.py` | Extend `ApplicationStatus` with `invited`, add `ApplicationInitiator` enum + `initiator` column on `Application`. |
| `backend/src/applications/schemas.py` | Add `ApplicationInitiator` to response; add `ApplicationInviteCreate` body schema. |
| `backend/src/applications/service.py` | Extend `VALID_TRANSITIONS`, extend actor rules in `update_status`, add `invite_student`. |
| `backend/src/applications/router.py` | Add `POST /invite`; extend `update_status` handler for new notification fan-out. |
| `backend/src/applications/repository.py` | Add `create_invite` helper (mirrors `create_application`). |
| `backend/src/users/router.py` | Add `GET /search`. |
| `backend/src/users/service.py` | Add `search_students`. |
| `backend/src/users/repository.py` | Add `search_students` — raw SQL via Tortoise for AND-skills + availability subquery. |
| `backend/src/users/schemas.py` | Add `StudentSearchItem` + `StudentSearchResponse`. |
| `backend/src/core/email.py` | Add `send_application_invite_email`. |
| `backend/src/tests/conftest.py` | Patch new email function (already patches `_send_smtp`, but we add an explicit spy to assert). |
| `backend/src/tests/test_invitations.py` | New — invite endpoint + transition/actor coverage. |
| `backend/src/tests/test_user_search.py` | New — search endpoint coverage. |
| `backend/migrations/models/2_XXXXXXXXXXXX_add_invited_status_and_initiator.py` | Aerich migration — additive only. |

### Frontend

| File | Role |
|------|------|
| `frontend/src/api/index.js` | Add `usersAPI.search` and `applicationsAPI.invite`. |
| `frontend/src/stores/applications.js` | Add `invite(payload)` action. |
| `frontend/src/components/StatusBadge.vue` | Add `invited` → blue variant. |
| `frontend/src/components/ApplicationDetailDrawer.vue` | Handle `invited` status for both `viewAs` branches. |
| `frontend/src/components/InviteStudentModal.vue` | New — project picker + message textarea. |
| `frontend/src/views/StudentsPage.vue` | New — search + filter + grid of student cards. |
| `frontend/src/views/MyApplicationsPage.vue` | Card footer text differentiates invited vs applied. |
| `frontend/src/views/ProfilePage.vue` | Invite button next to Edit; mount modal. |
| `frontend/src/router/index.js` | Register `/students` with role guard. |
| `frontend/src/components/AppNavbar.vue` | Add "Students" link for companies in desktop nav and mobile drawer. |

---

## Task 1 — Backend model, schema, migration

**Files:**
- Modify: `backend/src/applications/models.py`
- Modify: `backend/src/applications/schemas.py`
- Create: `backend/migrations/models/2_XXXXXXXXXXXX_add_invited_status_and_initiator.py`

Foundational task: DB column + enum + schema field. No endpoint changes yet.

- [ ] **Step 1: Extend `ApplicationStatus` and add `ApplicationInitiator`**

Replace the top of `backend/src/applications/models.py` with:

```python
import enum
from tortoise import fields, models


class ApplicationStatus(str, enum.Enum):
    invited = "invited"
    pending = "pending"
    accepted = "accepted"
    rejected = "rejected"
    in_progress = "in_progress"
    submitted = "submitted"
    revision_requested = "revision_requested"
    approved = "approved"
    completed = "completed"


class ApplicationInitiator(str, enum.Enum):
    student = "student"
    company = "company"


class Application(models.Model):
    id = fields.IntField(primary_key=True)
    project = fields.ForeignKeyField("models.Project", related_name="applications", on_delete=fields.CASCADE)
    applicant = fields.ForeignKeyField("models.User", related_name="applications", on_delete=fields.CASCADE)
    cover_letter = fields.TextField(null=True)
    status = fields.CharEnumField(enum_type=ApplicationStatus, default=ApplicationStatus.pending)
    initiator = fields.CharEnumField(enum_type=ApplicationInitiator, default=ApplicationInitiator.student)
    submission_note = fields.TextField(null=True)
    revision_note = fields.TextField(null=True)
    created_at = fields.DatetimeField(auto_now_add=True)
    updated_at = fields.DatetimeField(auto_now=True)
    status_history = fields.JSONField(default=list)

    class Meta:
        table = "applications"
        unique_together = (("project", "applicant"),)
```

- [ ] **Step 2: Extend `ApplicationResponse` and add invite body schema**

Edit `backend/src/applications/schemas.py` — add the `ApplicationInitiator` import, the `initiator` field on `ApplicationResponse`, and a new request body:

```python
from datetime import datetime
from typing import Optional
from pydantic import BaseModel, Field
from src.applications.models import ApplicationStatus, ApplicationInitiator


class ApplicationCreate(BaseModel):
    project_id: int
    cover_letter: Optional[str] = None


class ApplicationInviteCreate(BaseModel):
    project_id: int
    student_id: int
    message: Optional[str] = Field(None, max_length=2000)


class ApplicationUpdateStatus(BaseModel):
    status: ApplicationStatus
    note: Optional[str] = None


class StatusHistoryEntry(BaseModel):
    status: str
    timestamp: datetime
    actor_id: Optional[int] = None
    actor_name: str
    note: Optional[str] = None


class ApplicationResponse(BaseModel):
    id: int
    project_id: int
    applicant_id: int
    cover_letter: Optional[str] = None
    status: ApplicationStatus
    initiator: ApplicationInitiator
    submission_note: Optional[str] = None
    revision_note: Optional[str] = None
    status_history: list[StatusHistoryEntry] = []
    created_at: datetime
    updated_at: datetime

    class Config:
        from_attributes = True
```

- [ ] **Step 3: Generate migration**

Run from `backend/`:
```bash
aerich migrate --name "add_invited_status_and_initiator"
```

Aerich inspects the model diff and emits a new file under `backend/migrations/models/`. Expected content (timestamp varies; body should be equivalent):

```python
from tortoise import BaseDBAsyncClient


async def upgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "applications" ADD "initiator" VARCHAR(7) NOT NULL DEFAULT 'student';
        ALTER TABLE "applications" ALTER COLUMN "status" TYPE VARCHAR(18);"""


async def downgrade(db: BaseDBAsyncClient) -> str:
    return """
        ALTER TABLE "applications" DROP COLUMN "initiator";"""
```

If the emitted migration differs in quoting or `VARCHAR(N)` length, that is fine — Aerich is authoritative. The only requirement is that `initiator` has a default so existing rows backfill, and that nothing else in the schema is accidentally altered.

- [ ] **Step 4: Run the full backend test suite to confirm nothing broke**

Run from `backend/`:
```bash
pytest src/tests/ -v
```

Expected: all existing tests (~93) pass. Tortoise generates its test schema from `TEST_MODELS` in `conftest.py`, so adding the new enum value and column is automatic for tests — no Aerich involvement in SQLite memory mode.

- [ ] **Step 5: Commit**

```bash
git add backend/src/applications/models.py backend/src/applications/schemas.py backend/migrations/models/
git commit -m "feat(applications): add invited status and initiator field"
```

---

## Task 2 — Backend: transitions and actor rules for invited

**Files:**
- Modify: `backend/src/applications/service.py`
- Test: `backend/src/tests/test_invitations.py` (new file)

Extend the state machine so that `invited → accepted` is allowed by the student and `invited → rejected` is allowed by either the student (decline) or the project owner (withdraw). No new endpoint yet — tests use the existing `PUT /:id/status` and pre-seed a row with `status=invited`.

- [ ] **Step 1: Write a failing test for student-accepts-invite**

Create `backend/src/tests/test_invitations.py`:

```python
import pytest
from httpx import AsyncClient
from src.tests.conftest import auth
from src.applications.models import Application, ApplicationStatus, ApplicationInitiator


async def _seed_invite(client, company_token, student_token, title="Invite Project"):
    """Create a project and return (project_id, company_id, student_id, invite_app_id)."""
    r = await client.post("/api/v1/projects/", json={
        "title": title, "description": "Company invites a student to work on this."
    }, headers=auth(company_token))
    assert r.status_code == 201
    project_id = r.json()["id"]

    company_me = (await client.get("/api/v1/auth/me", headers=auth(company_token))).json()
    student_me = (await client.get("/api/v1/auth/me", headers=auth(student_token))).json()

    app = await Application.create(
        project_id=project_id,
        applicant_id=student_me["id"],
        cover_letter="Come build with us!",
        status=ApplicationStatus.invited,
        initiator=ApplicationInitiator.company,
        status_history=[{
            "status": "invited",
            "timestamp": "2026-04-15T00:00:00+00:00",
            "actor_id": company_me["id"],
            "actor_name": "company1",
            "note": None,
        }],
    )
    return project_id, company_me["id"], student_me["id"], app.id


@pytest.mark.asyncio
async def test_student_can_accept_invite(
    client: AsyncClient, company_token: str, student_token: str
):
    _, _, student_id, app_id = await _seed_invite(client, company_token, student_token)

    r = await client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "accepted"}, headers=auth(student_token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "accepted"
    assert body["status_history"][-1]["status"] == "accepted"
    assert body["status_history"][-1]["actor_id"] == student_id
```

- [ ] **Step 2: Run test to verify it fails**

Run from `backend/`:
```bash
pytest src/tests/test_invitations.py::test_student_can_accept_invite -v
```

Expected: FAIL with 400 "Cannot transition from invited to accepted".

- [ ] **Step 3: Add `invited` to `VALID_TRANSITIONS` and extend actor rules**

Edit `backend/src/applications/service.py`. Replace the `VALID_TRANSITIONS` dict and the permission block inside `update_status`:

```python
VALID_TRANSITIONS = {
    ApplicationStatus.invited: [ApplicationStatus.accepted, ApplicationStatus.rejected],
    ApplicationStatus.pending: [ApplicationStatus.accepted, ApplicationStatus.rejected],
    ApplicationStatus.accepted: [ApplicationStatus.in_progress],
    ApplicationStatus.in_progress: [ApplicationStatus.submitted],
    ApplicationStatus.submitted: [ApplicationStatus.approved, ApplicationStatus.revision_requested],
    ApplicationStatus.revision_requested: [ApplicationStatus.submitted],
    ApplicationStatus.approved: [ApplicationStatus.completed],
}
```

Inside `update_status`, replace the permission block (currently the `if new_status in owner_statuses ...` / `if new_status in applicant_statuses ...` pair) with:

```python
    is_owner = project.owner_id == user.id
    is_applicant = application.applicant_id == user.id
    is_admin = user.role == RoleEnum.admin

    owner_statuses = {ApplicationStatus.accepted, ApplicationStatus.rejected,
                      ApplicationStatus.approved, ApplicationStatus.revision_requested,
                      ApplicationStatus.completed}
    applicant_statuses = {ApplicationStatus.in_progress, ApplicationStatus.submitted}

    if application.status == ApplicationStatus.invited:
        # Student accepts or declines. Owner may only "withdraw" (reject).
        if new_status == ApplicationStatus.accepted and not (is_applicant or is_admin):
            raise HTTPException(status_code=403, detail="Only the invited student can accept")
        if new_status == ApplicationStatus.rejected and not (is_applicant or is_owner or is_admin):
            raise HTTPException(status_code=403, detail="Only the student or project owner can cancel an invite")
    else:
        if new_status in owner_statuses and not (is_owner or is_admin):
            raise HTTPException(status_code=403, detail="Only project owner can perform this action")
        if new_status in applicant_statuses and not is_applicant:
            raise HTTPException(status_code=403, detail="Only applicant can perform this action")
```

- [ ] **Step 4: Run test to verify it passes**

Run from `backend/`:
```bash
pytest src/tests/test_invitations.py::test_student_can_accept_invite -v
```

Expected: PASS.

- [ ] **Step 5: Add tests for decline, company-withdraw, third-party 403, and invalid transition**

Append to `backend/src/tests/test_invitations.py`:

```python
@pytest.mark.asyncio
async def test_student_can_decline_invite_with_note(
    client: AsyncClient, company_token: str, student_token: str
):
    _, _, student_id, app_id = await _seed_invite(client, company_token, student_token)

    r = await client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "rejected", "note": "timing is bad for me"},
        headers=auth(student_token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "rejected"
    assert body["status_history"][-1]["actor_id"] == student_id
    assert body["status_history"][-1]["note"] == "timing is bad for me"


@pytest.mark.asyncio
async def test_company_can_withdraw_invite(
    client: AsyncClient, company_token: str, student_token: str
):
    _, company_id, _, app_id = await _seed_invite(client, company_token, student_token)

    r = await client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "rejected"}, headers=auth(company_token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["status"] == "rejected"
    assert body["status_history"][-1]["actor_id"] == company_id


@pytest.mark.asyncio
async def test_third_party_cannot_respond_to_invite(
    client: AsyncClient, company_token: str, student_token: str
):
    _, _, _, app_id = await _seed_invite(client, company_token, student_token)

    # Register a second student (not the invitee)
    await client.post("/api/v1/auth/register", json={
        "email": "s2@test.com", "username": "student2",
        "password": "pass123", "role": "student",
    })
    # Mark verified via email-verify token in the mock redis store
    from src.tests.conftest import mock_redis_store
    for key in list(mock_redis_store):
        if key.startswith("email_verify:"):
            token = key.split(":", 1)[1]
            await client.get(f"/api/v1/auth/verify-email?token={token}")
    login = await client.post("/api/v1/auth/login",
                              data={"username": "student2", "password": "pass123"})
    other_token = login.json()["access_token"]

    r = await client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "accepted"}, headers=auth(other_token),
    )
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_invited_cannot_jump_to_in_progress(
    client: AsyncClient, company_token: str, student_token: str
):
    _, _, _, app_id = await _seed_invite(client, company_token, student_token)

    r = await client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "in_progress"}, headers=auth(student_token),
    )
    assert r.status_code == 400
    assert "Cannot transition" in r.json()["detail"]
```

- [ ] **Step 6: Run all new tests to verify they pass**

Run from `backend/`:
```bash
pytest src/tests/test_invitations.py -v
```

Expected: 4 tests PASS.

- [ ] **Step 7: Run full suite to confirm no regression**

Run from `backend/`:
```bash
pytest src/tests/ -v
```

Expected: all tests pass.

- [ ] **Step 8: Commit**

```bash
git add backend/src/applications/service.py backend/src/tests/test_invitations.py
git commit -m "feat(applications): handle invited status transitions and actor rules"
```

---

## Task 3 — Backend: `POST /applications/invite` endpoint

**Files:**
- Modify: `backend/src/applications/repository.py`
- Modify: `backend/src/applications/service.py`
- Modify: `backend/src/applications/router.py`
- Test: `backend/src/tests/test_invitations.py` (append)

- [ ] **Step 1: Write the failing happy-path test**

Append to `backend/src/tests/test_invitations.py`:

```python
async def _create_open_project(client, company_token, title="Invite me", max_participants=2):
    r = await client.post("/api/v1/projects/", json={
        "title": title, "description": "desc", "max_participants": max_participants,
    }, headers=auth(company_token))
    return r.json()["id"]


@pytest.mark.asyncio
async def test_invite_student_happy_path(
    client: AsyncClient, company_token: str, student_token: str
):
    project_id = await _create_open_project(client, company_token)
    student_id = (await client.get("/api/v1/auth/me", headers=auth(student_token))).json()["id"]

    r = await client.post("/api/v1/applications/invite", json={
        "project_id": project_id, "student_id": student_id,
        "message": "We'd love to have you on this.",
    }, headers=auth(company_token))
    assert r.status_code == 201
    body = r.json()
    assert body["status"] == "invited"
    assert body["initiator"] == "company"
    assert body["applicant_id"] == student_id
    assert body["cover_letter"] == "We'd love to have you on this."
    assert len(body["status_history"]) == 1
    assert body["status_history"][0]["status"] == "invited"
```

- [ ] **Step 2: Run test to verify it fails**

Run from `backend/`:
```bash
pytest src/tests/test_invitations.py::test_invite_student_happy_path -v
```

Expected: FAIL with 404 (route does not exist yet).

- [ ] **Step 3: Add `create_invite` to the repository**

Append to `backend/src/applications/repository.py`:

```python
async def create_invite(project_id: int, student_id: int,
                        message: str | None) -> Application:
    return await Application.create(
        project_id=project_id,
        applicant_id=student_id,
        cover_letter=message,
        status=ApplicationStatus.invited,
        initiator=ApplicationInitiator.company,
    )
```

And update the imports at the top:
```python
from src.applications.models import Application, ApplicationStatus, ApplicationInitiator
```

- [ ] **Step 4: Add `invite_student` to the service**

Append to `backend/src/applications/service.py`:

```python
async def invite_student(user: User, project_id: int, student_id: int,
                         message: str | None) -> tuple[Application, Project, User]:
    if user.role != RoleEnum.company:
        raise HTTPException(status_code=403, detail="Only companies can send invites")

    project = await Project.filter(id=project_id).first()
    if not project:
        raise HTTPException(status_code=404, detail="Project not found")
    if project.owner_id != user.id:
        raise HTTPException(status_code=403, detail="Not your project")
    if project.status.value != "open":
        raise HTTPException(status_code=400, detail="Project is not open")

    student = await User.filter(id=student_id).first()
    if not student:
        raise HTTPException(status_code=404, detail="Student not found")
    if student.role != RoleEnum.student:
        raise HTTPException(status_code=400, detail="Target user is not a student")

    if await repository.exists(project_id, student_id):
        raise HTTPException(status_code=400, detail="Student already invited or applied to this project")

    active_count = await repository.count_active(project_id)
    if active_count >= project.max_participants:
        raise HTTPException(status_code=400, detail="Project has reached maximum number of participants")

    application = await repository.create_invite(project_id, student_id, message)
    application.status_history = _append_history(application, "invited", user, None)
    await repository.save(application)

    await log_activity(user.id, "invite",
                       f"Invited {student.username} to '{project.title}'",
                       "application", application.id)

    return application, project, student
```

- [ ] **Step 5: Wire the route**

Edit `backend/src/applications/router.py`. Add the import and the new handler. Note: email fan-out and notifications are added in Task 4 — this task only creates the row and returns it.

Add imports at the top:
```python
from src.applications.schemas import (
    ApplicationCreate, ApplicationUpdateStatus, ApplicationResponse,
    ApplicationInviteCreate,
)
```

Add the handler below the existing `apply` route:
```python
@router.post("/invite", response_model=ApplicationResponse, status_code=201)
async def invite_student(data: ApplicationInviteCreate, bg: BackgroundTasks,
                         current_user: User = Depends(get_current_user)):
    application, project, student = await service.invite_student(
        current_user, data.project_id, data.student_id, data.message,
    )
    # Notification + email fan-out is added in Task 4.
    return application
```

- [ ] **Step 6: Run test to verify it passes**

Run from `backend/`:
```bash
pytest src/tests/test_invitations.py::test_invite_student_happy_path -v
```

Expected: PASS.

- [ ] **Step 7: Add guard-coverage tests**

Append to `backend/src/tests/test_invitations.py`:

```python
@pytest.mark.asyncio
async def test_only_company_can_invite(
    client: AsyncClient, company_token: str, student_token: str
):
    # Company creates a project, then a student tries to invite themselves — should 403.
    project_id = await _create_open_project(client, company_token)
    student_id = (await client.get("/api/v1/auth/me", headers=auth(student_token))).json()["id"]
    r = await client.post("/api/v1/applications/invite", json={
        "project_id": project_id, "student_id": student_id,
    }, headers=auth(student_token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_invite_requires_project_ownership(
    client: AsyncClient, student_token: str
):
    """A company that doesn't own the project can't invite to it."""
    # Register a second company
    await client.post("/api/v1/auth/register", json={
        "email": "c2@test.com", "username": "company2",
        "password": "pass123", "role": "company",
    })
    from src.tests.conftest import mock_redis_store
    for key in list(mock_redis_store):
        if key.startswith("email_verify:"):
            token = key.split(":", 1)[1]
            await client.get(f"/api/v1/auth/verify-email?token={token}")
    other_login = await client.post("/api/v1/auth/login",
                                    data={"username": "company2", "password": "pass123"})
    other_company_token = other_login.json()["access_token"]

    # The primary company fixture doesn't exist in this test, so register one:
    await client.post("/api/v1/auth/register", json={
        "email": "c1@test.com", "username": "company1b",
        "password": "pass123", "role": "company",
    })
    for key in list(mock_redis_store):
        if key.startswith("email_verify:"):
            token = key.split(":", 1)[1]
            await client.get(f"/api/v1/auth/verify-email?token={token}")
    primary_login = await client.post("/api/v1/auth/login",
                                      data={"username": "company1b", "password": "pass123"})
    primary_token = primary_login.json()["access_token"]
    project_id = await _create_open_project(client, primary_token)

    student_id = (await client.get("/api/v1/auth/me", headers=auth(student_token))).json()["id"]
    r = await client.post("/api/v1/applications/invite", json={
        "project_id": project_id, "student_id": student_id,
    }, headers=auth(other_company_token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_invite_non_student_is_rejected(
    client: AsyncClient, company_token: str
):
    # Invite another company as if they were a student.
    await client.post("/api/v1/auth/register", json={
        "email": "c2@test.com", "username": "company2",
        "password": "pass123", "role": "company",
    })
    from src.tests.conftest import mock_redis_store
    for key in list(mock_redis_store):
        if key.startswith("email_verify:"):
            token = key.split(":", 1)[1]
            await client.get(f"/api/v1/auth/verify-email?token={token}")
    other = (await client.post("/api/v1/auth/login",
                               data={"username": "company2", "password": "pass123"})).json()
    project_id = await _create_open_project(client, company_token)
    other_me = (await client.get("/api/v1/auth/me",
                                  headers=auth(other["access_token"]))).json()

    r = await client.post("/api/v1/applications/invite", json={
        "project_id": project_id, "student_id": other_me["id"],
    }, headers=auth(company_token))
    assert r.status_code == 400
    assert "not a student" in r.json()["detail"]


@pytest.mark.asyncio
async def test_invite_duplicate_blocked(
    client: AsyncClient, company_token: str, student_token: str
):
    project_id = await _create_open_project(client, company_token)
    student_id = (await client.get("/api/v1/auth/me", headers=auth(student_token))).json()["id"]

    first = await client.post("/api/v1/applications/invite", json={
        "project_id": project_id, "student_id": student_id,
    }, headers=auth(company_token))
    assert first.status_code == 201

    second = await client.post("/api/v1/applications/invite", json={
        "project_id": project_id, "student_id": student_id,
    }, headers=auth(company_token))
    assert second.status_code == 400
    assert "already invited or applied" in second.json()["detail"]


@pytest.mark.asyncio
async def test_invite_full_project_blocked(
    client: AsyncClient, company_token: str, student_token: str
):
    # max_participants=1, and we'll reserve that slot with another accepted student.
    project_id = await _create_open_project(client, company_token, max_participants=1)
    # First student applies and is accepted
    await client.post("/api/v1/auth/register", json={
        "email": "s3@test.com", "username": "student3",
        "password": "pass123", "role": "student",
    })
    from src.tests.conftest import mock_redis_store
    for key in list(mock_redis_store):
        if key.startswith("email_verify:"):
            token = key.split(":", 1)[1]
            await client.get(f"/api/v1/auth/verify-email?token={token}")
    s3 = (await client.post("/api/v1/auth/login",
                            data={"username": "student3", "password": "pass123"})).json()
    s3_token = s3["access_token"]
    apply_r = await client.post("/api/v1/applications/",
                                json={"project_id": project_id}, headers=auth(s3_token))
    await client.put(f"/api/v1/applications/{apply_r.json()['id']}/status",
                     json={"status": "accepted"}, headers=auth(company_token))

    # Now try to invite a different student — project is full.
    student_id = (await client.get("/api/v1/auth/me", headers=auth(student_token))).json()["id"]
    r = await client.post("/api/v1/applications/invite", json={
        "project_id": project_id, "student_id": student_id,
    }, headers=auth(company_token))
    assert r.status_code == 400
    assert "maximum number of participants" in r.json()["detail"]
```

- [ ] **Step 8: Run new tests**

Run from `backend/`:
```bash
pytest src/tests/test_invitations.py -v
```

Expected: all 9 tests PASS.

- [ ] **Step 9: Run full suite**

Run from `backend/`:
```bash
pytest src/tests/ -v
```

Expected: all pass.

- [ ] **Step 10: Commit**

```bash
git add backend/src/applications/router.py backend/src/applications/service.py backend/src/applications/repository.py backend/src/tests/test_invitations.py
git commit -m "feat(applications): add POST /applications/invite endpoint"
```

---

## Task 4 — Backend: notifications and email on invite lifecycle

**Files:**
- Modify: `backend/src/core/email.py`
- Modify: `backend/src/applications/router.py`
- Test: `backend/src/tests/test_invitations.py` (append)

Wire `create_notification` calls and a best-effort invite email. Four events: company invites student, student accepts invite, student declines invite, company withdraws invite.

- [ ] **Step 1: Add the invite email template**

Append to `backend/src/core/email.py`:

```python
async def send_application_invite_email(to_email: str, username: str,
                                        project_title: str, company_name: str):
    html = _base_template(
        "You've been invited to a project",
        f"<p>Hi <strong>{username}</strong>,</p>"
        f'<p><strong>{company_name}</strong> has invited you to join <strong>"{project_title}"</strong>.</p>'
        '<p><a href="http://localhost:3000/my-applications" style="color:#e8a838">Review Invitation →</a></p>'
    )
    await _send_smtp(to_email, f"Invitation: {project_title}", html)
```

(No config toggle is needed — `_send_smtp` already no-ops when `SMTP_USER`/`SMTP_PASSWORD` are unset, matching the deployment in `DEPLOY.md`.)

- [ ] **Step 2: Write the failing notification-and-email test**

Append to `backend/src/tests/test_invitations.py`. The notification is asserted by reading `mock_mongo.notifications.docs`. The email call is asserted by spying on the background-task scheduler; `_send_smtp` is already patched in `conftest.py`, so we verify the scheduled call via `unittest.mock.patch` at the import site.

```python
from unittest.mock import AsyncMock, patch
from src.tests.conftest import mock_mongo


@pytest.mark.asyncio
async def test_invite_creates_notification_and_schedules_email(
    client: AsyncClient, company_token: str, student_token: str
):
    project_id = await _create_open_project(client, company_token, title="Cool Project")
    student_id = (await client.get("/api/v1/auth/me", headers=auth(student_token))).json()["id"]

    with patch("src.applications.router.send_application_invite_email",
               new_callable=AsyncMock) as email_mock:
        r = await client.post("/api/v1/applications/invite", json={
            "project_id": project_id, "student_id": student_id,
            "message": "Hi there!",
        }, headers=auth(company_token))
    assert r.status_code == 201

    # Notification inserted for the student
    notifs = [d for d in mock_mongo.notifications.docs if d["user_id"] == student_id]
    assert len(notifs) == 1
    assert notifs[0]["notification_type"] == "invite"
    assert "Cool Project" in notifs[0]["title"]
    assert notifs[0]["link"] == "/my-applications"

    # Email scheduled via BackgroundTasks
    email_mock.assert_called_once()
    args, _kw = email_mock.call_args
    assert args[2] == "Cool Project"   # project_title argument
```

- [ ] **Step 3: Run test to verify it fails**

Run from `backend/`:
```bash
pytest src/tests/test_invitations.py::test_invite_creates_notification_and_schedules_email -v
```

Expected: FAIL — notification list is empty, email mock never called.

- [ ] **Step 4: Wire notification + email into the invite route**

Edit `backend/src/applications/router.py`. Update the imports and the invite handler:

```python
from fastapi import APIRouter, Depends, BackgroundTasks, Query
from src.core.dependencies import get_current_user
from src.core.email import (
    send_application_status_email, send_new_application_email,
    send_submission_email, send_application_invite_email,
)
from src.notifications.service import create_notification
from src.users.models import User
from src.applications.models import ApplicationStatus
from src.applications import service
from src.applications.schemas import (
    ApplicationCreate, ApplicationUpdateStatus, ApplicationResponse,
    ApplicationInviteCreate,
)

router = APIRouter(prefix="/applications", tags=["Applications"])
```

Replace the invite handler body with:

```python
@router.post("/invite", response_model=ApplicationResponse, status_code=201)
async def invite_student(data: ApplicationInviteCreate, bg: BackgroundTasks,
                         current_user: User = Depends(get_current_user)):
    application, project, student = await service.invite_student(
        current_user, data.project_id, data.student_id, data.message,
    )
    company_name = current_user.full_name or current_user.username
    await create_notification(
        student.id,
        title=f"Invitation to {project.title}",
        message=f"{company_name} invited you to join this project.",
        notification_type="invite",
        link="/my-applications",
    )
    bg.add_task(send_application_invite_email, student.email, student.username,
                project.title, company_name)
    return application
```

- [ ] **Step 5: Run the invite-notification test**

Run from `backend/`:
```bash
pytest src/tests/test_invitations.py::test_invite_creates_notification_and_schedules_email -v
```

Expected: PASS.

- [ ] **Step 6: Wire invite-lifecycle notifications into update_status**

Edit `backend/src/applications/router.py` — extend the existing `update_status` handler to notify on the three new lifecycle events. Replace the handler body:

```python
@router.put("/{app_id}/status", response_model=ApplicationResponse)
async def update_status(app_id: int, data: ApplicationUpdateStatus, bg: BackgroundTasks,
                        current_user: User = Depends(get_current_user)):
    # Capture previous status before service mutates the row (needed for invite-lifecycle fan-out).
    from src.applications import repository as apps_repo
    prev = await apps_repo.get_by_id(app_id)
    prev_status = prev.status if prev else None
    was_initiator_company = prev.initiator.value == "company" if prev else False

    application, project = await service.update_status(
        app_id, data.status, data.note, current_user,
    )

    owner_statuses = {ApplicationStatus.accepted, ApplicationStatus.rejected,
                      ApplicationStatus.approved, ApplicationStatus.revision_requested,
                      ApplicationStatus.completed}

    applicant = await User.filter(id=application.applicant_id).first()
    owner = await User.filter(id=project.owner_id).first()

    # Existing fan-out (email only) preserved below.
    if applicant:
        if data.status in owner_statuses:
            bg.add_task(send_application_status_email, applicant.email, applicant.username,
                        project.title, data.status.value)
        elif data.status == ApplicationStatus.submitted:
            if owner:
                bg.add_task(send_submission_email, owner.email, owner.username,
                            project.title, applicant.username)

    # Invite lifecycle notifications
    if prev_status == ApplicationStatus.invited and was_initiator_company:
        if data.status == ApplicationStatus.accepted and owner:
            await create_notification(
                owner.id,
                title=f"{applicant.username} accepted your invitation",
                message=f"For project '{project.title}'.",
                notification_type="info",
                link=f"/projects/{project.id}",
            )
        elif data.status == ApplicationStatus.rejected:
            # Differentiate student-decline vs company-withdraw by actor
            if current_user.id == application.applicant_id and owner:
                await create_notification(
                    owner.id,
                    title=f"{applicant.username} declined your invitation",
                    message=f"For project '{project.title}'.",
                    notification_type="info",
                    link=f"/projects/{project.id}",
                )
            elif current_user.id == project.owner_id and applicant:
                await create_notification(
                    applicant.id,
                    title=f"Invitation withdrawn: {project.title}",
                    message="The company cancelled this invitation.",
                    notification_type="info",
                    link="/my-applications",
                )
    return application
```

- [ ] **Step 7: Add tests for accept/decline/withdraw notifications**

Append to `backend/src/tests/test_invitations.py`:

```python
@pytest.mark.asyncio
async def test_accept_invite_notifies_owner(
    client: AsyncClient, company_token: str, student_token: str
):
    _, company_id, _, app_id = await _seed_invite(client, company_token, student_token)
    mock_mongo.notifications.docs.clear()

    await client.put(f"/api/v1/applications/{app_id}/status",
                     json={"status": "accepted"}, headers=auth(student_token))

    notifs = [d for d in mock_mongo.notifications.docs if d["user_id"] == company_id]
    assert len(notifs) == 1
    assert "accepted" in notifs[0]["title"].lower()


@pytest.mark.asyncio
async def test_decline_invite_notifies_owner(
    client: AsyncClient, company_token: str, student_token: str
):
    _, company_id, _, app_id = await _seed_invite(client, company_token, student_token)
    mock_mongo.notifications.docs.clear()

    await client.put(f"/api/v1/applications/{app_id}/status",
                     json={"status": "rejected", "note": "not this time"},
                     headers=auth(student_token))

    notifs = [d for d in mock_mongo.notifications.docs if d["user_id"] == company_id]
    assert len(notifs) == 1
    assert "declined" in notifs[0]["title"].lower()


@pytest.mark.asyncio
async def test_withdraw_invite_notifies_student(
    client: AsyncClient, company_token: str, student_token: str
):
    _, _, student_id, app_id = await _seed_invite(client, company_token, student_token)
    mock_mongo.notifications.docs.clear()

    await client.put(f"/api/v1/applications/{app_id}/status",
                     json={"status": "rejected"}, headers=auth(company_token))

    notifs = [d for d in mock_mongo.notifications.docs if d["user_id"] == student_id]
    assert len(notifs) == 1
    assert "withdraw" in notifs[0]["title"].lower()
```

- [ ] **Step 8: Run invitation tests and full suite**

Run from `backend/`:
```bash
pytest src/tests/test_invitations.py -v
pytest src/tests/ -v
```

Expected: all pass.

- [ ] **Step 9: Commit**

```bash
git add backend/src/core/email.py backend/src/applications/router.py backend/src/tests/test_invitations.py
git commit -m "feat(applications): notifications and invite email for invite lifecycle"
```

---

## Task 5 — Backend: `GET /users/search`

**Files:**
- Modify: `backend/src/users/repository.py`
- Modify: `backend/src/users/service.py`
- Modify: `backend/src/users/router.py`
- Modify: `backend/src/users/schemas.py`
- Modify: `backend/src/tests/conftest.py` (add the new cache mock at this import site)
- Test: `backend/src/tests/test_user_search.py` (new file)

Adds a company-only search endpoint that filters students by skills (AND), min_rating, availability, and free-text `q`.

- [ ] **Step 1: Add response schemas**

Append to `backend/src/users/schemas.py`:

```python
class StudentSearchItem(BaseModel):
    id: int
    username: str
    full_name: Optional[str] = None
    avatar_url: Optional[str] = None
    bio: Optional[str] = None
    skills: list[SkillOut] = []
    rating: float = 0.0
    completed_projects_count: int = 0
    is_available: bool = True
    class Config:
        from_attributes = True


class StudentSearchResponse(BaseModel):
    items: list[StudentSearchItem]
    total: int
    page: int
    size: int
```

- [ ] **Step 2: Add the repository query**

Append to `backend/src/users/repository.py`:

```python
from tortoise.expressions import Q
from src.applications.models import Application, ApplicationStatus


async def search_students(skill_ids: list[int] | None, min_rating: float | None,
                          available: bool, q_str: str | None,
                          offset: int, limit: int) -> tuple[list[User], int]:
    qs = User.filter(role="student", is_active=True, is_blocked=False)

    if q_str:
        qs = qs.filter(Q(username__icontains=q_str) | Q(full_name__icontains=q_str))

    if skill_ids:
        # AND semantics: user must have every requested skill.
        for sid in skill_ids:
            qs = qs.filter(skills__id=sid)
        qs = qs.distinct()

    if min_rating is not None:
        qs = qs.filter(student_profile__rating__gte=min_rating)

    if available:
        active_statuses = (
            ApplicationStatus.accepted, ApplicationStatus.in_progress,
            ApplicationStatus.submitted, ApplicationStatus.revision_requested,
            ApplicationStatus.approved,
        )
        busy_ids = await Application.filter(
            status__in=active_statuses,
        ).values_list("applicant_id", flat=True)
        if busy_ids:
            qs = qs.exclude(id__in=list(set(busy_ids)))

    total = await qs.count()
    items = await qs.prefetch_related("skills", "student_profile").offset(offset).limit(limit)
    return items, total


async def active_app_exists_for(user_id: int) -> bool:
    from src.applications.models import ApplicationStatus
    active = (ApplicationStatus.accepted, ApplicationStatus.in_progress,
              ApplicationStatus.submitted, ApplicationStatus.revision_requested,
              ApplicationStatus.approved)
    return await Application.filter(applicant_id=user_id, status__in=active).exists()
```

- [ ] **Step 3: Add the service method**

Append to `backend/src/users/service.py`, extending the `UserService` class:

```python
    async def search_students(self, skill_ids: list[int] | None,
                              min_rating: float | None, available: bool,
                              q: str | None, page: int, size: int) -> dict:
        cache_key = (f"userSearch:{sorted(skill_ids or [])}:{min_rating}:"
                     f"{int(available)}:{q or ''}:{page}:{size}")
        cached = await cache_get(cache_key)
        if cached:
            return cached

        offset = (page - 1) * size
        items, total = await repository.search_students(
            skill_ids, min_rating, available, q, offset, size,
        )

        result_items = []
        for u in items:
            profile = u.student_profile if hasattr(u, "student_profile") else None
            rating = profile.rating if profile else 0.0
            completed = profile.completed_projects_count if profile else 0
            is_available = not await repository.active_app_exists_for(u.id)
            result_items.append({
                "id": u.id,
                "username": u.username,
                "full_name": u.full_name,
                "avatar_url": u.avatar_url,
                "bio": u.bio,
                "skills": [{"id": s.id, "name": s.name, "category": s.category} for s in u.skills],
                "rating": rating,
                "completed_projects_count": completed,
                "is_available": is_available,
            })

        payload = {"items": result_items, "total": total, "page": page, "size": size}
        await cache_set(cache_key, payload, ttl=60)
        return payload
```

Ensure the imports at the top already include `cache_get`, `cache_set` (they do).

- [ ] **Step 4: Wire the route**

Edit `backend/src/users/router.py` — add the search route. Add imports:

```python
from typing import Optional
from fastapi import APIRouter, Depends, Query
from src.core.dependencies import get_current_user
from src.users.models import User, RoleEnum
from src.users.schemas import (
    UserResponse, UserUpdate,
    CompanyProfileCreate, CompanyProfileResponse,
    StudentProfileCreate, StudentProfileResponse,
    StudentSearchResponse,
)
from src.users.service import UserService
from fastapi import HTTPException
```

Add the handler near the top of the router (before `get_user`, because FastAPI matches routes in declaration order and `/search` must win over `/{user_id}`):

```python
@router.get("/search", response_model=StudentSearchResponse)
async def search_students(
    skills: list[int] = Query(default=[]),
    min_rating: Optional[float] = Query(None, ge=0, le=5),
    available: bool = Query(False),
    q: Optional[str] = Query(None, min_length=1, max_length=100),
    page: int = Query(1, ge=1),
    size: int = Query(20, ge=1, le=50),
    current_user: User = Depends(get_current_user),
):
    if current_user.role not in (RoleEnum.company, RoleEnum.admin):
        raise HTTPException(status_code=403, detail="Only companies can search students")
    return await UserService().search_students(
        skill_ids=skills or None,
        min_rating=min_rating,
        available=available,
        q=q,
        page=page,
        size=size,
    )
```

- [ ] **Step 5: Patch new cache calls in conftest**

The new `search_students` service method uses `cache_get`/`cache_set`, and the existing PATCHES list already covers `src.users.service.cache_get` and `src.users.service.cache_set`. Verify:

```bash
grep -n "src.users.service.cache" backend/src/tests/conftest.py
```

Expected output includes both entries. No change needed.

- [ ] **Step 6: Write the test file**

Create `backend/src/tests/test_user_search.py`:

```python
import pytest
from httpx import AsyncClient
from src.tests.conftest import auth, mock_redis_store, _register_and_verify
from src.users.models import User, StudentProfile
from src.skills.models import Skill


async def _create_student(client: AsyncClient, email: str, username: str) -> tuple[str, int]:
    token = await _register_and_verify(client, email, username, "pass123", "student")
    me = (await client.get("/api/v1/auth/me", headers=auth(token))).json()
    return token, me["id"]


@pytest.mark.asyncio
async def test_search_requires_company_role(
    client: AsyncClient, student_token: str
):
    r = await client.get("/api/v1/users/search", headers=auth(student_token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_search_returns_students_only(
    client: AsyncClient, company_token: str, student_token: str
):
    r = await client.get("/api/v1/users/search", headers=auth(company_token))
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["username"] == "student1"


@pytest.mark.asyncio
async def test_search_by_skills_AND(
    client: AsyncClient, company_token: str, student_token: str
):
    # Create a second student with only one of the two skills
    _, s2_id = await _create_student(client, "s2@test.com", "student2")

    # Seed skills
    py = await Skill.create(name="Python", category="language")
    docker = await Skill.create(name="Docker", category="tool")

    # student1 has both
    me_r = await client.get("/api/v1/auth/me", headers=auth(student_token))
    s1 = await User.filter(id=me_r.json()["id"]).first()
    await s1.skills.add(py)
    await s1.skills.add(docker)

    # student2 has only Python
    s2 = await User.filter(id=s2_id).first()
    await s2.skills.add(py)

    r = await client.get(
        f"/api/v1/users/search?skills={py.id}&skills={docker.id}",
        headers=auth(company_token),
    )
    assert r.status_code == 200
    body = r.json()
    assert body["total"] == 1
    assert body["items"][0]["username"] == "student1"


@pytest.mark.asyncio
async def test_search_min_rating(
    client: AsyncClient, company_token: str, student_token: str
):
    # Promote student1's rating
    me_r = await client.get("/api/v1/auth/me", headers=auth(student_token))
    await StudentProfile.filter(user_id=me_r.json()["id"]).update(rating=4.5)

    r = await client.get("/api/v1/users/search?min_rating=4.0",
                         headers=auth(company_token))
    assert r.status_code == 200
    assert r.json()["total"] == 1

    r = await client.get("/api/v1/users/search?min_rating=4.8",
                         headers=auth(company_token))
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_search_available_excludes_active(
    client: AsyncClient, company_token: str, student_token: str
):
    # student1 applies and is accepted (= not available)
    proj = await client.post("/api/v1/projects/", json={
        "title": "Busy work", "description": "."
    }, headers=auth(company_token))
    pid = proj.json()["id"]
    app_r = await client.post("/api/v1/applications/",
                              json={"project_id": pid}, headers=auth(student_token))
    await client.put(f"/api/v1/applications/{app_r.json()['id']}/status",
                     json={"status": "accepted"}, headers=auth(company_token))

    r = await client.get("/api/v1/users/search?available=true",
                         headers=auth(company_token))
    assert r.json()["total"] == 0

    r = await client.get("/api/v1/users/search?available=false",
                         headers=auth(company_token))
    assert r.json()["total"] == 1


@pytest.mark.asyncio
async def test_search_text_match(
    client: AsyncClient, company_token: str, student_token: str
):
    # student1 is already registered from the fixture
    r = await client.get("/api/v1/users/search?q=student1", headers=auth(company_token))
    assert r.json()["total"] == 1

    r = await client.get("/api/v1/users/search?q=nobody", headers=auth(company_token))
    assert r.json()["total"] == 0


@pytest.mark.asyncio
async def test_search_pagination(
    client: AsyncClient, company_token: str, student_token: str
):
    for i in range(2, 8):
        await _create_student(client, f"s{i}@test.com", f"student{i}")

    r = await client.get("/api/v1/users/search?page=1&size=3",
                         headers=auth(company_token))
    body = r.json()
    assert body["total"] == 7
    assert len(body["items"]) == 3
    assert body["page"] == 1

    r2 = await client.get("/api/v1/users/search?page=3&size=3",
                          headers=auth(company_token))
    assert len(r2.json()["items"]) == 1
```

- [ ] **Step 7: Run the new test file**

Run from `backend/`:
```bash
pytest src/tests/test_user_search.py -v
```

Expected: all 7 tests PASS.

- [ ] **Step 8: Run full suite**

Run from `backend/`:
```bash
pytest src/tests/ -v
```

Expected: all pass.

- [ ] **Step 9: Commit**

```bash
git add backend/src/users/router.py backend/src/users/service.py backend/src/users/repository.py backend/src/users/schemas.py backend/src/tests/test_user_search.py
git commit -m "feat(users): add GET /users/search endpoint for company-side student search"
```

---

## Task 6 — Frontend: API client, store, status badge

**Files:**
- Modify: `frontend/src/api/index.js`
- Modify: `frontend/src/stores/applications.js`
- Modify: `frontend/src/components/StatusBadge.vue`

No tests (the codebase has no Vue test harness per `CLAUDE.md`); verified visually later.

- [ ] **Step 1: Add API client methods**

Edit `frontend/src/api/index.js`. Add one line to `usersAPI` (search) and one to `applicationsAPI` (invite):

```js
// ── Users ───────────────────────────────────────────
export const usersAPI = {
  get: id => api.get(`/users/${id}`),
  update: (id, d) => api.put(`/users/${id}`, d),
  addSkill: (uid, sid) => api.post(`/users/${uid}/skills/${sid}`),
  removeSkill: (uid, sid) => api.delete(`/users/${uid}/skills/${sid}`),
  getCompanyProfile: id => api.get(`/users/${id}/company-profile`),
  updateCompanyProfile: (id, d) => api.put(`/users/${id}/company-profile`, d),
  getStudentProfile: id => api.get(`/users/${id}/student-profile`),
  updateStudentProfile: (id, d) => api.put(`/users/${id}/student-profile`, d),
  search: params => api.get('/users/search', { params }),
}
```

```js
// ── Applications ────────────────────────────────────
export const applicationsAPI = {
  apply: d => api.post('/applications/', d),
  invite: d => api.post('/applications/invite', d),
  updateStatus: (id, d) => api.put(`/applications/${id}/status`, d),
  byProject: pid => api.get(`/applications/project/${pid}`),
  my: () => api.get('/applications/my'),
}
```

- [ ] **Step 2: Add invite action to the store**

Edit `frontend/src/stores/applications.js`. Add one action between `apply` and `updateStatus`:

```js
  async function invite(payload) {
    const { data } = await applicationsAPI.invite(payload)
    return data
  }
```

And add `invite` to the return object:
```js
  return { myApps, byProject, loading, error, fetchMy, fetchByProject, apply, invite, updateStatus }
```

- [ ] **Step 3: Add the `invited` variant to StatusBadge**

Edit `frontend/src/components/StatusBadge.vue`. Add one key to `colorMap` and one CSS class:

```js
const colorMap = {
  open: 'status-green',
  in_progress: 'status-amber',
  closed: 'status-red',
  rejected: 'status-red',
  revision_requested: 'status-red',
  pending: 'status-gray',
  invited: 'status-blue',
  accepted: 'status-green',
  approved: 'status-green',
  completed: 'status-green',
  submitted: 'status-purple',
}
```

Append to the `<style scoped>` block:

```css
.status-blue {
  background: #dbeafe;
  color: #1d4ed8;
}
[data-theme="dark"] .status-blue {
  background: #1e3a8a;
  color: #bfdbfe;
}
```

- [ ] **Step 4: Build and confirm no errors**

Run from `frontend/`:
```bash
npm run build
```

Expected: build succeeds without errors. No test suite on frontend to run.

- [ ] **Step 5: Commit**

```bash
git add frontend/src/api/index.js frontend/src/stores/applications.js frontend/src/components/StatusBadge.vue
git commit -m "feat(frontend): invite API client, store action, and invited status badge"
```

---

## Task 7 — Frontend: ApplicationDetailDrawer + MyApplicationsPage

**Files:**
- Modify: `frontend/src/components/ApplicationDetailDrawer.vue`
- Modify: `frontend/src/views/MyApplicationsPage.vue`

- [ ] **Step 1: Extend `actionButtons` in the drawer**

Edit `frontend/src/components/ApplicationDetailDrawer.vue`. Replace the `actionButtons` computed:

```js
const actionButtons = computed(() => {
  if (!props.application) return []
  const s = props.application.status
  if (props.viewAs === 'student') {
    if (s === 'invited') return [
      { status: 'accepted', label: 'Accept Invitation', icon: 'check', class: 'btn btn-primary btn-sm' },
      { status: 'rejected', label: 'Decline', icon: 'close', class: 'btn btn-danger btn-sm', requiresNote: true },
    ]
    if (s === 'accepted') return [{ status: 'in_progress', label: 'Start Working', icon: 'play_arrow', class: 'btn btn-primary btn-sm' }]
    if (s === 'in_progress' || s === 'revision_requested') return [{ status: 'submitted', label: 'Submit Work', icon: 'send', class: 'btn btn-primary btn-sm', requiresNote: true }]
    return []
  }
  if (props.viewAs === 'company') {
    if (s === 'invited') return [
      { status: 'rejected', label: 'Withdraw Invite', icon: 'undo', class: 'btn btn-ghost btn-sm' },
    ]
    if (s === 'pending') return [
      { status: 'accepted', label: 'Accept', icon: 'check', class: 'btn btn-primary btn-sm' },
      { status: 'rejected', label: 'Reject', icon: 'close', class: 'btn btn-danger btn-sm' },
    ]
    if (s === 'submitted') return [
      { status: 'approved', label: 'Approve', icon: 'check_circle', class: 'btn btn-primary btn-sm' },
      { status: 'revision_requested', label: 'Request Revision', icon: 'edit_note', class: 'btn btn-outline btn-sm', requiresNote: true },
    ]
    if (s === 'approved') return [{ status: 'completed', label: 'Mark Completed', icon: 'task_alt', class: 'btn btn-primary btn-sm' }]
  }
  return []
})
```

- [ ] **Step 2: Update MyApplicationsPage footer line for invited state**

Edit `frontend/src/views/MyApplicationsPage.vue`. Replace the `STATUS_LABELS` map and `latestSummary` function:

```js
const STATUS_LABELS = {
  invited: 'Invited',
  pending: 'Pending', accepted: 'Accepted', rejected: 'Rejected',
  in_progress: 'In Progress', submitted: 'Submitted',
  revision_requested: 'Revision Requested', approved: 'Approved', completed: 'Completed',
}

function latestSummary(app) {
  if (app.status === 'invited' && app.initiator === 'company') {
    return 'You were invited — awaiting your response'
  }
  const hist = app.status_history || []
  if (!hist.length) return `Applied ${fmtDate(app.created_at)}`
  const latest = hist[hist.length - 1]
  return `Latest: ${STATUS_LABELS[latest.status] || latest.status} · ${fmtDate(latest.timestamp)}`
}
```

- [ ] **Step 3: Build and smoke-test in browser**

Run the backend and frontend:
```bash
docker compose up -d postgres mongo redis minio
cd backend && uvicorn src.main:app --reload --port 8000 &
cd frontend && npm run dev
```

Manually verify:
1. Seed an `invited` application for a student via `psql` or the API (the invite endpoint from Task 4).
2. Log in as that student → go to `/my-applications` → card shows "Invited" badge (blue) and footer "You were invited — awaiting your response".
3. Click card → drawer opens with "Accept Invitation" + "Decline" buttons.
4. Click Accept → row transitions to `accepted`; card updates in place.
5. For a second invited row, click Decline → note box appears → type a reason → Confirm → row transitions to `rejected`.

- [ ] **Step 4: Commit**

```bash
git add frontend/src/components/ApplicationDetailDrawer.vue frontend/src/views/MyApplicationsPage.vue
git commit -m "feat(frontend): render invite accept/decline actions for students"
```

---

## Task 8 — Frontend: InviteStudentModal

**Files:**
- Create: `frontend/src/components/InviteStudentModal.vue`

- [ ] **Step 1: Create the modal component**

Create `frontend/src/components/InviteStudentModal.vue`:

```vue
<template>
  <BaseModal :modelValue="modelValue" @update:modelValue="$emit('update:modelValue', $event)"
             title="Invite to Project" maxWidth="480px">
    <div v-if="loading" class="loading-msg">Loading your projects...</div>
    <div v-else-if="!projects.length" class="empty-msg">
      <p>You have no open projects yet.</p>
      <router-link to="/projects/create" class="btn btn-primary btn-sm" @click="close">
        Create a Project
      </router-link>
    </div>
    <form v-else @submit.prevent="submit" class="invite-form">
      <FormField label="Project" :error="projectError">
        <select v-model="selectedProject" class="input select" required>
          <option value="" disabled>Choose one of your open projects</option>
          <option v-for="p in projects" :key="p.id" :value="p.id" :disabled="isFull(p)">
            {{ p.title }}{{ isFull(p) ? ' (full)' : '' }}
          </option>
        </select>
      </FormField>
      <FormField label="Message (optional)" hint="Will be shown to the student">
        <textarea class="input" v-model="message" rows="4"
                  placeholder="Tell them why you'd like them on this project..." maxlength="2000"></textarea>
      </FormField>
      <p v-if="errorMsg" class="invite-error">{{ errorMsg }}</p>
    </form>
    <template #footer>
      <button class="btn btn-ghost btn-sm" @click="close" :disabled="busy">Cancel</button>
      <button v-if="projects.length" class="btn btn-primary btn-sm"
              :disabled="!selectedProject || busy" @click="submit">
        {{ busy ? 'Sending...' : 'Send Invitation' }}
      </button>
    </template>
  </BaseModal>
</template>

<script setup>
import { ref, watch, computed } from 'vue'
import { useAuthStore } from '@/stores/auth'
import { useApplicationsStore } from '@/stores/applications'
import { projectsAPI } from '@/api'
import BaseModal from '@/components/BaseModal.vue'
import FormField from '@/components/FormField.vue'

const props = defineProps({
  modelValue: { type: Boolean, required: true },
  studentId: { type: Number, required: true },
})
const emit = defineEmits(['update:modelValue', 'sent'])

const auth = useAuthStore()
const applications = useApplicationsStore()
const loading = ref(false)
const busy = ref(false)
const projects = ref([])
const selectedProject = ref('')
const message = ref('')
const errorMsg = ref('')
const projectError = computed(() => '')

async function loadProjects() {
  if (!auth.user?.id) return
  loading.value = true
  try {
    const { data } = await projectsAPI.list({
      owner_id: auth.user.id, status: 'open', size: 50,
    })
    projects.value = data.items || []
  } catch {
    projects.value = []
  } finally {
    loading.value = false
  }
}

function isFull(p) {
  return typeof p.active_count === 'number' && p.active_count >= p.max_participants
}

async function submit() {
  if (!selectedProject.value) return
  busy.value = true
  errorMsg.value = ''
  try {
    await applications.invite({
      project_id: selectedProject.value,
      student_id: props.studentId,
      message: message.value || null,
    })
    emit('sent')
    reset()
    close()
  } catch (err) {
    errorMsg.value = err.response?.data?.detail || 'Could not send invitation.'
  } finally {
    busy.value = false
  }
}

function reset() {
  selectedProject.value = ''
  message.value = ''
  errorMsg.value = ''
}

function close() {
  if (busy.value) return
  emit('update:modelValue', false)
}

watch(() => props.modelValue, (open) => {
  if (open) {
    reset()
    loadProjects()
  }
})
</script>

<style scoped>
.invite-form { display: flex; flex-direction: column; gap: 14px; }
.loading-msg, .empty-msg { padding: 16px; text-align: center; color: var(--gray-500); font-size: .8125rem; }
.empty-msg .btn { margin-top: 10px; }
.invite-error {
  color: var(--danger); font-size: .8125rem;
  background: var(--danger-light); padding: 8px 12px;
  border-radius: var(--radius-md); margin: 0;
}
.input.select { width: 100%; }
</style>
```

Note on the `isFull` guard: the backend `Project` response does not currently expose `active_count`. Until it does, `isFull` always returns false and the backend's capacity guard is what actually blocks over-capacity invites (returning the 400 that lands in `errorMsg`). This is fine — UI shows all open projects, and an over-capacity attempt surfaces the backend error inline.

- [ ] **Step 2: Build to confirm no errors**

Run from `frontend/`:
```bash
npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Commit**

```bash
git add frontend/src/components/InviteStudentModal.vue
git commit -m "feat(frontend): InviteStudentModal with project picker and message"
```

---

## Task 9 — Frontend: StudentsPage, route, nav, and profile invite button

**Files:**
- Create: `frontend/src/views/StudentsPage.vue`
- Modify: `frontend/src/router/index.js`
- Modify: `frontend/src/components/AppNavbar.vue`
- Modify: `frontend/src/views/ProfilePage.vue`

- [ ] **Step 1: Create the students list page**

Create `frontend/src/views/StudentsPage.vue`:

```vue
<template>
  <div class="page container">
    <header class="page-header">
      <div>
        <h1>Students</h1>
        <p class="page-sub">{{ total }} students {{ availableOnly ? 'available' : 'registered' }}</p>
      </div>
    </header>

    <div class="filters-bar">
      <div class="search-box">
        <span class="material-icons-round">search</span>
        <input class="input" v-model="q" placeholder="Search by name or username..." @input="debouncedFetch" />
      </div>
      <div class="filter-group">
        <input class="input" type="number" v-model.number="minRating" step="0.5" min="0" max="5"
               placeholder="Min rating" style="width:120px" @change="resetAndFetch" />
        <label class="avail-toggle">
          <input type="checkbox" v-model="availableOnly" @change="resetAndFetch" />
          Available only
        </label>
      </div>
    </div>

    <div class="skills-filter">
      <SkillPicker :skills="selectedSkills" :editable="true"
                   :userId="null" @updated="onSkillsUpdate" />
    </div>

    <div v-if="loading" class="grid">
      <div v-for="n in 6" :key="n" class="card">
        <SkeletonBlock height="18px" width="60%" />
        <div style="margin-top:10px"><SkeletonBlock height="12px" width="40%" /></div>
      </div>
    </div>
    <div v-else-if="students.length" class="grid">
      <router-link v-for="s in students" :key="s.id"
                   :to="`/profile/${s.id}`" class="student-card card">
        <div class="student-head">
          <div class="student-avatar">{{ (s.full_name || s.username)[0].toUpperCase() }}</div>
          <div class="student-info">
            <div class="student-name">{{ s.full_name || s.username }}</div>
            <div class="student-meta">
              <span v-if="s.rating">⭐ {{ s.rating.toFixed(1) }}</span>
              <span>· {{ s.completed_projects_count }} completed</span>
              <span v-if="s.is_available" class="avail-chip">Available</span>
            </div>
          </div>
        </div>
        <div v-if="s.skills?.length" class="skills-row">
          <span v-for="sk in s.skills.slice(0,4)" :key="sk.id" class="skill-chip">{{ sk.name }}</span>
          <span v-if="s.skills.length > 4" class="skill-chip">+{{ s.skills.length - 4 }}</span>
        </div>
        <button class="btn btn-primary btn-sm invite-btn" @click.prevent.stop="openInvite(s)">
          <span class="material-icons-round">person_add</span>Invite
        </button>
      </router-link>
    </div>
    <EmptyState v-else icon="search_off" title="No students match" subtitle="Adjust the filters to see more." />

    <div v-if="totalPages > 1" class="pagination">
      <button class="btn btn-ghost btn-sm" :disabled="page <= 1" @click="page--; fetch()">
        <span class="material-icons-round">chevron_left</span>
      </button>
      <span class="page-info">{{ page }} / {{ totalPages }}</span>
      <button class="btn btn-ghost btn-sm" :disabled="page >= totalPages" @click="page++; fetch()">
        <span class="material-icons-round">chevron_right</span>
      </button>
    </div>

    <InviteStudentModal v-if="inviteTarget" v-model="inviteOpen" :studentId="inviteTarget.id" />
  </div>
</template>

<script setup>
import { ref, computed, onMounted, onUnmounted } from 'vue'
import { usersAPI } from '@/api'
import SkeletonBlock from '@/components/SkeletonBlock.vue'
import EmptyState from '@/components/EmptyState.vue'
import SkillPicker from '@/components/SkillPicker.vue'
import InviteStudentModal from '@/components/InviteStudentModal.vue'

const students = ref([])
const total = ref(0)
const loading = ref(false)
const page = ref(1)
const size = 12
const q = ref('')
const minRating = ref(null)
const availableOnly = ref(false)
const selectedSkills = ref([])

const inviteOpen = ref(false)
const inviteTarget = ref(null)

const totalPages = computed(() => Math.ceil(total.value / size))

function openInvite(student) {
  inviteTarget.value = student
  inviteOpen.value = true
}

function onSkillsUpdate(skills) {
  selectedSkills.value = skills || []
  resetAndFetch()
}

let timer
function debouncedFetch() {
  clearTimeout(timer)
  timer = setTimeout(() => { page.value = 1; fetch() }, 300)
}
onUnmounted(() => clearTimeout(timer))

function resetAndFetch() {
  page.value = 1
  fetch()
}

async function fetch() {
  loading.value = true
  const params = { page: page.value, size }
  if (q.value) params.q = q.value
  if (minRating.value !== null && minRating.value !== '') params.min_rating = minRating.value
  if (availableOnly.value) params.available = true
  if (selectedSkills.value.length) params.skills = selectedSkills.value.map(s => s.id)
  try {
    const { data } = await usersAPI.search(params)
    students.value = data.items
    total.value = data.total
  } catch {
    students.value = []
    total.value = 0
  } finally {
    loading.value = false
  }
}

onMounted(fetch)
</script>

<style scoped>
.page { padding: 2rem 24px; }
.page-header { margin-bottom: 1.5rem; }
.page-sub { color: var(--gray-400); font-size: .8125rem; margin-top: 2px; }
.filters-bar { display: flex; gap: 10px; margin-bottom: 1rem; flex-wrap: wrap; }
.search-box { flex: 1; min-width: 220px; position: relative; display: flex; align-items: center; }
.search-box .material-icons-round { position: absolute; left: 12px; color: var(--gray-400); font-size: 18px; }
.search-box .input { padding-left: 36px; width: 100%; }
.filter-group { display: flex; align-items: center; gap: 10px; }
.avail-toggle { display: flex; align-items: center; gap: 6px; font-size: .8125rem; color: var(--gray-600); }
.skills-filter { margin-bottom: 1.5rem; }
.grid { display: grid; grid-template-columns: repeat(auto-fill, minmax(300px, 1fr)); gap: 16px; }
.student-card {
  padding: 16px; text-decoration: none; color: inherit;
  display: flex; flex-direction: column; gap: 12px;
  border: 1px solid var(--gray-200); border-radius: var(--radius-lg); background: var(--white);
  transition: all .15s ease;
}
.student-card:hover { border-color: var(--gray-300); box-shadow: var(--shadow-sm); }
.student-head { display: flex; gap: 12px; align-items: center; }
.student-avatar {
  width: 44px; height: 44px; border-radius: 50%; background: var(--accent); color: white;
  display: flex; align-items: center; justify-content: center; font-weight: 600;
}
.student-info { flex: 1; min-width: 0; }
.student-name { font-weight: 600; color: var(--gray-900); font-size: .9375rem; }
.student-meta { display: flex; flex-wrap: wrap; gap: 8px; font-size: .75rem; color: var(--gray-500); margin-top: 2px; }
.avail-chip { background: #dcfce7; color: #166534; padding: 1px 8px; border-radius: 12px; }
.skills-row { display: flex; gap: 6px; flex-wrap: wrap; }
.skill-chip { background: var(--gray-100); color: var(--gray-700); padding: 2px 8px; border-radius: 12px; font-size: .75rem; }
.invite-btn { justify-content: center; margin-top: auto; }
.pagination { display: flex; align-items: center; justify-content: center; gap: 12px; margin-top: 1.5rem; }
.page-info { font-size: .8125rem; color: var(--gray-500); }
</style>
```

- [ ] **Step 2: Register the route**

Edit `frontend/src/router/index.js`. Add one entry inside the `routes` array, before the catch-all:

```js
  { path: '/students', name: 'Students', component: () => import('@/views/StudentsPage.vue'), meta: { auth: true, roles: ['company', 'admin'] } },
```

- [ ] **Step 3: Add the Students nav link for companies**

Edit `frontend/src/components/AppNavbar.vue`. In the desktop `.nav-links` block, add after "Projects":

```html
        <router-link v-if="auth.isCompany || auth.isAdmin" to="/students" class="nav-link">Students</router-link>
```

And in the mobile `.drawer-links` block, after "Projects":

```html
            <router-link v-if="auth.isCompany || auth.isAdmin" to="/students" class="drawer-link" @click="drawerOpen = false">
              <span class="material-icons-round">groups</span>Students
            </router-link>
```

- [ ] **Step 4: Add Invite button on ProfilePage**

Edit `frontend/src/views/ProfilePage.vue`. In the template, replace the `<button v-if="isMe" ...>` Edit button block with:

```html
      <button v-if="isMe" class="btn btn-secondary btn-sm" @click="showEdit = true">
        <span class="material-icons-round">edit</span>Edit
      </button>
      <button v-else-if="canInvite" class="btn btn-primary btn-sm" @click="showInvite = true">
        <span class="material-icons-round">person_add</span>Invite to Project
      </button>
```

At the end of the `<template>` (alongside `EditProfileModal`), add:

```html
    <InviteStudentModal v-if="user && canInvite" v-model="showInvite" :studentId="user.id" />
```

Inside the `<script setup>`, add the import and state:

```js
import InviteStudentModal from '@/components/InviteStudentModal.vue'
```

Add alongside `showEdit`:
```js
const showInvite = ref(false)
```

Add a computed:
```js
const canInvite = computed(() => auth.user?.role === 'company' && isStudent.value && !isMe.value)
```

- [ ] **Step 5: Build + manual smoke test**

Run from `frontend/`:
```bash
npm run build
```

Start the stack and verify:
1. Log in as a company.
2. Nav shows "Students" link. Click it → `/students` loads with filter controls and student cards.
3. Apply a skill filter via `SkillPicker` and a min rating → list updates.
4. Click "Invite" on a card → modal opens with the company's open projects in the dropdown.
5. Pick a project, write a message, submit → toast/success path (modal closes). Verify a new row in the `applications` table (e.g. `docker compose exec postgres psql -U postgres platform_db -c "SELECT id, status, initiator FROM applications ORDER BY id DESC LIMIT 1;"`).
6. Log in as that student → `/my-applications` shows the invited card. Accept → status flips.
7. Open the student's profile as the company → "Invite to Project" button visible next to name; clicking opens the same modal.
8. As a student, visit `/students` directly — should redirect away (route guard).

- [ ] **Step 6: Commit**

```bash
git add frontend/src/views/StudentsPage.vue frontend/src/router/index.js frontend/src/components/AppNavbar.vue frontend/src/views/ProfilePage.vue
git commit -m "feat(frontend): students search page, nav link, and profile invite button"
```

---

## Final verification

- [ ] **Step 1: Run the full backend test suite**

```bash
cd backend && pytest src/tests/ -v
```

Expected: ~113 tests pass (93 prior + ~20 new).

- [ ] **Step 2: Build the frontend**

```bash
cd frontend && npm run build
```

Expected: build succeeds.

- [ ] **Step 3: Run the full feature manually end-to-end**

Using Docker Compose:
```bash
docker compose up --build
```

Scenarios to exercise:
1. Company invites student → student sees notification + invited card on `/my-applications`.
2. Student accepts → becomes team member, appears on project board, card shows "Accepted".
3. Student declines with a note → company sees decline notification.
4. Company withdraws an invited row → student sees "Invitation withdrawn".
5. Duplicate invite attempt to same project → 400 surfaced inline in modal.
6. Invite to different open project after a decline → succeeds.
7. Search with two skills (AND), min_rating, and available toggle → filters apply correctly.
8. Student visits `/students` → redirected (role guard).
9. Invite email: with `SMTP_USER`/`SMTP_PASSWORD` unset, no error; invite HTTP response is 201 regardless. With them set, email lands.
