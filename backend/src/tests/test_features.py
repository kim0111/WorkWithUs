import pytest
from httpx import AsyncClient
from src.tests.conftest import auth


# ── Application Tests (Workflow) ─────────────────────

@pytest.mark.asyncio
async def test_apply_to_project(client: AsyncClient, company_token: str, student_token: str):
    proj = await client.post("/api/v1/projects/", json={
        "title": "Apply Here", "description": "Open for applications"
    }, headers=auth(company_token))
    pid = proj.json()["id"]

    r = await client.post("/api/v1/applications/", json={
        "project_id": pid, "cover_letter": "I'm very interested!"
    }, headers=auth(student_token))
    assert r.status_code == 201
    assert r.json()["status"] == "pending"


@pytest.mark.asyncio
async def test_apply_duplicate(client: AsyncClient, company_token: str, student_token: str):
    proj = await client.post("/api/v1/projects/", json={
        "title": "No Dup", "description": "No duplicate applications"
    }, headers=auth(company_token))
    pid = proj.json()["id"]

    await client.post("/api/v1/applications/", json={"project_id": pid}, headers=auth(student_token))
    r = await client.post("/api/v1/applications/", json={"project_id": pid}, headers=auth(student_token))
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_company_cant_apply(client: AsyncClient, company_token: str):
    proj = await client.post("/api/v1/projects/", json={
        "title": "Own Project", "description": "Can't apply to own"
    }, headers=auth(company_token))
    r = await client.post("/api/v1/applications/", json={"project_id": proj.json()["id"]},
                          headers=auth(company_token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_application_workflow_accept(client: AsyncClient, company_token: str, student_token: str):
    """Full workflow: pending → accepted → in_progress → submitted → approved → completed"""
    proj = await client.post("/api/v1/projects/", json={
        "title": "Workflow Test", "description": "Testing the full workflow"
    }, headers=auth(company_token))
    pid = proj.json()["id"]

    app = await client.post("/api/v1/applications/", json={"project_id": pid}, headers=auth(student_token))
    aid = app.json()["id"]

    # Owner accepts
    r = await client.put(f"/api/v1/applications/{aid}/status",
                         json={"status": "accepted"}, headers=auth(company_token))
    assert r.status_code == 200
    assert r.json()["status"] == "accepted"

    # Student starts work
    r = await client.put(f"/api/v1/applications/{aid}/status",
                         json={"status": "in_progress"}, headers=auth(student_token))
    assert r.json()["status"] == "in_progress"

    # Student submits
    r = await client.put(f"/api/v1/applications/{aid}/status",
                         json={"status": "submitted", "note": "Work is done"}, headers=auth(student_token))
    assert r.json()["status"] == "submitted"

    # Owner approves
    r = await client.put(f"/api/v1/applications/{aid}/status",
                         json={"status": "approved"}, headers=auth(company_token))
    assert r.json()["status"] == "approved"

    # Owner completes
    r = await client.put(f"/api/v1/applications/{aid}/status",
                         json={"status": "completed"}, headers=auth(company_token))
    assert r.json()["status"] == "completed"


@pytest.mark.asyncio
async def test_application_reject(client: AsyncClient, company_token: str, student_token: str):
    proj = await client.post("/api/v1/projects/", json={
        "title": "Reject Test", "description": "Will reject this application"
    }, headers=auth(company_token))

    app = await client.post("/api/v1/applications/", json={"project_id": proj.json()["id"]},
                            headers=auth(student_token))
    r = await client.put(f"/api/v1/applications/{app.json()['id']}/status",
                         json={"status": "rejected"}, headers=auth(company_token))
    assert r.json()["status"] == "rejected"


@pytest.mark.asyncio
async def test_invalid_transition(client: AsyncClient, company_token: str, student_token: str):
    proj = await client.post("/api/v1/projects/", json={
        "title": "Bad Trans", "description": "Invalid status transition"
    }, headers=auth(company_token))

    app = await client.post("/api/v1/applications/", json={"project_id": proj.json()["id"]},
                            headers=auth(student_token))
    # Try to go from pending → completed (invalid)
    r = await client.put(f"/api/v1/applications/{app.json()['id']}/status",
                         json={"status": "completed"}, headers=auth(company_token))
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_revision_workflow(client: AsyncClient, company_token: str, student_token: str):
    proj = await client.post("/api/v1/projects/", json={
        "title": "Revision Test", "description": "Test revision request"
    }, headers=auth(company_token))
    app = await client.post("/api/v1/applications/", json={"project_id": proj.json()["id"]},
                            headers=auth(student_token))
    aid = app.json()["id"]

    # Accept → In Progress → Submit → Revision → Resubmit → Approve
    await client.put(f"/api/v1/applications/{aid}/status", json={"status": "accepted"}, headers=auth(company_token))
    await client.put(f"/api/v1/applications/{aid}/status", json={"status": "in_progress"}, headers=auth(student_token))
    await client.put(f"/api/v1/applications/{aid}/status", json={"status": "submitted"}, headers=auth(student_token))

    r = await client.put(f"/api/v1/applications/{aid}/status",
                         json={"status": "revision_requested", "note": "Fix the header"}, headers=auth(company_token))
    assert r.json()["status"] == "revision_requested"

    r = await client.put(f"/api/v1/applications/{aid}/status",
                         json={"status": "submitted", "note": "Fixed!"}, headers=auth(student_token))
    assert r.json()["status"] == "submitted"


@pytest.mark.asyncio
async def test_get_my_applications(client: AsyncClient, company_token: str, student_token: str):
    proj = await client.post("/api/v1/projects/", json={
        "title": "My Apps", "description": "Test my applications list"
    }, headers=auth(company_token))
    await client.post("/api/v1/applications/", json={"project_id": proj.json()["id"]},
                      headers=auth(student_token))
    r = await client.get("/api/v1/applications/my", headers=auth(student_token))
    assert r.status_code == 200
    assert len(r.json()) >= 1


@pytest.mark.asyncio
async def test_get_project_applications(client: AsyncClient, company_token: str, student_token: str):
    proj = await client.post("/api/v1/projects/", json={
        "title": "Proj Apps", "description": "Test project applications list"
    }, headers=auth(company_token))
    pid = proj.json()["id"]
    await client.post("/api/v1/applications/", json={"project_id": pid}, headers=auth(student_token))
    r = await client.get(f"/api/v1/applications/project/{pid}", headers=auth(company_token))
    assert r.status_code == 200
    assert len(r.json()) >= 1


# ── Reviews Tests ────────────────────────────────────

@pytest.mark.asyncio
async def test_create_review_after_approval(client: AsyncClient, company_token: str, student_token: str):
    # Setup: create project, apply, go through workflow to approved
    proj = await client.post("/api/v1/projects/", json={
        "title": "Review Test", "description": "Test bidirectional reviews"
    }, headers=auth(company_token))
    pid = proj.json()["id"]

    app = await client.post("/api/v1/applications/", json={"project_id": pid}, headers=auth(student_token))
    aid = app.json()["id"]

    await client.put(f"/api/v1/applications/{aid}/status", json={"status": "accepted"}, headers=auth(company_token))
    await client.put(f"/api/v1/applications/{aid}/status", json={"status": "in_progress"}, headers=auth(student_token))
    await client.put(f"/api/v1/applications/{aid}/status", json={"status": "submitted"}, headers=auth(student_token))
    await client.put(f"/api/v1/applications/{aid}/status", json={"status": "approved"}, headers=auth(company_token))

    # Company reviews student
    me_student = await client.get("/api/v1/auth/me", headers=auth(student_token))
    sid = me_student.json()["id"]

    r = await client.post("/api/v1/reviews/", json={
        "reviewee_id": sid, "project_id": pid, "application_id": aid,
        "rating": 4.5, "comment": "Great work!"
    }, headers=auth(company_token))
    assert r.status_code == 201
    assert r.json()["review_type"] == "owner_to_student"

    # Student reviews company
    me_company = await client.get("/api/v1/auth/me", headers=auth(company_token))
    cid = me_company.json()["id"]

    r = await client.post("/api/v1/reviews/", json={
        "reviewee_id": cid, "project_id": pid, "rating": 5.0, "comment": "Amazing project!"
    }, headers=auth(student_token))
    assert r.status_code == 201
    assert r.json()["review_type"] == "student_to_owner"


@pytest.mark.asyncio
async def test_cant_review_self(client: AsyncClient, student_token: str):
    me = await client.get("/api/v1/auth/me", headers=auth(student_token))
    r = await client.post("/api/v1/reviews/", json={
        "reviewee_id": me.json()["id"], "project_id": 1, "rating": 5.0
    }, headers=auth(student_token))
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_get_user_reviews(client: AsyncClient, student_token: str):
    me = await client.get("/api/v1/auth/me", headers=auth(student_token))
    r = await client.get(f"/api/v1/reviews/user/{me.json()['id']}")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_get_user_rating(client: AsyncClient, student_token: str):
    me = await client.get("/api/v1/auth/me", headers=auth(student_token))
    r = await client.get(f"/api/v1/reviews/user/{me.json()['id']}/rating")
    assert r.status_code == 200
    assert "average_rating" in r.json()


# ── Portfolio Tests ──────────────────────────────────

@pytest.mark.asyncio
async def test_add_portfolio_item(client: AsyncClient, student_token: str):
    r = await client.post("/api/v1/portfolio/", json={
        "title": "My First Project", "description": "Built an app",
        "project_url": "https://github.com/me/project"
    }, headers=auth(student_token))
    assert r.status_code == 201
    assert r.json()["title"] == "My First Project"


@pytest.mark.asyncio
async def test_company_cant_add_portfolio(client: AsyncClient, company_token: str):
    r = await client.post("/api/v1/portfolio/", json={"title": "Nope"},
                          headers=auth(company_token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_get_portfolio(client: AsyncClient, student_token: str):
    me = await client.get("/api/v1/auth/me", headers=auth(student_token))
    await client.post("/api/v1/portfolio/", json={"title": "Portfolio Item"},
                      headers=auth(student_token))
    r = await client.get(f"/api/v1/portfolio/user/{me.json()['id']}")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_delete_portfolio_item(client: AsyncClient, student_token: str):
    item = await client.post("/api/v1/portfolio/", json={"title": "To Delete"},
                             headers=auth(student_token))
    r = await client.delete(f"/api/v1/portfolio/{item.json()['id']}", headers=auth(student_token))
    assert r.status_code == 204


# ── Notifications Tests (MongoDB-backed) ─────────────

@pytest.mark.asyncio
async def test_get_notifications(client: AsyncClient, student_token: str):
    r = await client.get("/api/v1/notifications/", headers=auth(student_token))
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_get_unread_count(client: AsyncClient, student_token: str):
    r = await client.get("/api/v1/notifications/unread-count", headers=auth(student_token))
    assert r.status_code == 200
    assert "count" in r.json()


@pytest.mark.asyncio
async def test_mark_all_read(client: AsyncClient, student_token: str):
    r = await client.post("/api/v1/notifications/read-all", headers=auth(student_token))
    assert r.status_code == 204


# ── Admin Tests ──────────────────────────────────────

@pytest.mark.asyncio
async def test_admin_stats(client: AsyncClient, admin_token: str):
    r = await client.get("/api/v1/admin/stats", headers=auth(admin_token))
    assert r.status_code == 200
    assert "total_users" in r.json()
    assert "total_chat_messages" in r.json()


@pytest.mark.asyncio
async def test_admin_stats_forbidden(client: AsyncClient, student_token: str):
    r = await client.get("/api/v1/admin/stats", headers=auth(student_token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_admin_list_users(client: AsyncClient, admin_token: str):
    r = await client.get("/api/v1/admin/users", headers=auth(admin_token))
    assert r.status_code == 200
    assert len(r.json()) >= 1


@pytest.mark.asyncio
async def test_admin_block_user(client: AsyncClient, admin_token: str, student_token: str):
    me = await client.get("/api/v1/auth/me", headers=auth(student_token))
    uid = me.json()["id"]
    r = await client.put(f"/api/v1/admin/users/{uid}", json={"is_blocked": True},
                         headers=auth(admin_token))
    assert r.status_code == 200
    assert r.json()["is_blocked"] is True


@pytest.mark.asyncio
async def test_admin_change_role(client: AsyncClient, admin_token: str):
    await client.post("/api/v1/auth/register", json={
        "email": "role@test.com", "username": "roleuser", "password": "pass123", "role": "student"
    })
    users = await client.get("/api/v1/admin/users", headers=auth(admin_token))
    target = [u for u in users.json() if u["username"] == "roleuser"]
    if target:
        r = await client.put(f"/api/v1/admin/users/{target[0]['id']}", json={"role": "committee"},
                             headers=auth(admin_token))
        assert r.status_code == 200
