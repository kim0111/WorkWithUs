import pytest
from httpx import AsyncClient
from src.tests.conftest import auth, _register_and_verify


# ── Helpers ─────────────────────────────────────────────

async def _create_project_with_team(client, company_token, student_token, max_participants=5):
    """Create a project, apply + accept the student — returns (project_id, student_user_id)."""
    proj = await client.post("/api/v1/projects/", json={
        "title": "Kanban Project", "description": "For task board testing",
        "max_participants": max_participants,
    }, headers=auth(company_token))
    pid = proj.json()["id"]

    app = await client.post("/api/v1/applications/", json={
        "project_id": pid, "cover_letter": "Let me in",
    }, headers=auth(student_token))
    aid = app.json()["id"]

    await client.put(f"/api/v1/applications/{aid}/status",
                     json={"status": "accepted"}, headers=auth(company_token))

    from src.users.models import User
    student = await User.filter(username="student1").first()
    return pid, student.id


# ── Create / List ──────────────────────────────────────

@pytest.mark.asyncio
async def test_owner_creates_task(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_with_team(client, company_token, student_token)
    r = await client.post(f"/api/v1/tasks/project/{pid}", json={
        "title": "Design login screen", "description": "Figma mock + review",
        "priority": "high",
    }, headers=auth(company_token))
    assert r.status_code == 201, r.text
    data = r.json()
    assert data["title"] == "Design login screen"
    assert data["status"] == "todo"
    assert data["priority"] == "high"
    assert data["project_id"] == pid


@pytest.mark.asyncio
async def test_list_tasks(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_with_team(client, company_token, student_token)
    for title in ("A", "B", "C"):
        await client.post(f"/api/v1/tasks/project/{pid}",
                          json={"title": title}, headers=auth(company_token))

    r = await client.get(f"/api/v1/tasks/project/{pid}", headers=auth(student_token))
    assert r.status_code == 200
    assert len(r.json()) == 3


@pytest.mark.asyncio
async def test_team_member_creates_task(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_with_team(client, company_token, student_token)
    r = await client.post(f"/api/v1/tasks/project/{pid}",
                          json={"title": "Student-created"}, headers=auth(student_token))
    assert r.status_code == 201


@pytest.mark.asyncio
async def test_outsider_cant_list_tasks(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_with_team(client, company_token, student_token)
    outsider = await _register_and_verify(client, "out@test.com", "outsider", "pass123", "student")
    r = await client.get(f"/api/v1/tasks/project/{pid}", headers=auth(outsider))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_outsider_cant_create_task(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_with_team(client, company_token, student_token)
    outsider = await _register_and_verify(client, "out2@test.com", "outsider2", "pass123", "student")
    r = await client.post(f"/api/v1/tasks/project/{pid}",
                          json={"title": "nope"}, headers=auth(outsider))
    assert r.status_code == 403


# ── Update / move column ───────────────────────────────

@pytest.mark.asyncio
async def test_move_task_logs_activity(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_with_team(client, company_token, student_token)
    created = await client.post(f"/api/v1/tasks/project/{pid}",
                                json={"title": "Move me"}, headers=auth(company_token))
    tid = created.json()["id"]

    r = await client.put(f"/api/v1/tasks/{tid}",
                         json={"status": "in_progress"}, headers=auth(student_token))
    assert r.status_code == 200
    assert r.json()["status"] == "in_progress"

    activity = await client.get(f"/api/v1/tasks/{tid}/activity", headers=auth(company_token))
    assert activity.status_code == 200
    actions = [a["action"] for a in activity.json()]
    assert "status" in actions
    assert "created" in actions


@pytest.mark.asyncio
async def test_update_priority(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_with_team(client, company_token, student_token)
    created = await client.post(f"/api/v1/tasks/project/{pid}",
                                json={"title": "Prio"}, headers=auth(company_token))
    tid = created.json()["id"]
    r = await client.put(f"/api/v1/tasks/{tid}",
                         json={"priority": "high"}, headers=auth(company_token))
    assert r.status_code == 200
    assert r.json()["priority"] == "high"


# ── Assignee ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_assign_team_member(client: AsyncClient, company_token, student_token):
    pid, sid = await _create_project_with_team(client, company_token, student_token)
    r = await client.post(f"/api/v1/tasks/project/{pid}", json={
        "title": "Assigned task", "assignee_id": sid,
    }, headers=auth(company_token))
    assert r.status_code == 201
    assert r.json()["assignee_id"] == sid
    assert r.json()["assignee_username"] == "student1"


@pytest.mark.asyncio
async def test_cant_assign_non_team_member(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_with_team(client, company_token, student_token)
    await _register_and_verify(client, "x@test.com", "xstudent", "pass123", "student")
    from src.users.models import User
    outsider = await User.filter(username="xstudent").first()

    r = await client.post(f"/api/v1/tasks/project/{pid}", json={
        "title": "Bad assign", "assignee_id": outsider.id,
    }, headers=auth(company_token))
    assert r.status_code == 400


# ── Delete ─────────────────────────────────────────────

@pytest.mark.asyncio
async def test_owner_deletes_task(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_with_team(client, company_token, student_token)
    created = await client.post(f"/api/v1/tasks/project/{pid}",
                                json={"title": "Delete me"}, headers=auth(company_token))
    tid = created.json()["id"]
    r = await client.delete(f"/api/v1/tasks/{tid}", headers=auth(company_token))
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_non_lead_cant_delete_task(client: AsyncClient, company_token, student_token):
    pid, sid = await _create_project_with_team(client, company_token, student_token)
    # Add a second student who is NOT the lead
    s2_token = await _register_and_verify(client, "s2@test.com", "student2", "pass123", "student")
    from src.users.models import User
    s2 = await User.filter(username="student2").first()
    await client.post(f"/api/v1/teams/project/{pid}/members",
                      json={"user_id": s2.id, "role": "frontend"},
                      headers=auth(company_token))

    created = await client.post(f"/api/v1/tasks/project/{pid}",
                                json={"title": "Protected"}, headers=auth(company_token))
    tid = created.json()["id"]
    r = await client.delete(f"/api/v1/tasks/{tid}", headers=auth(s2_token))
    assert r.status_code == 403


# ── Filters ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_filter_by_priority(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_with_team(client, company_token, student_token)
    await client.post(f"/api/v1/tasks/project/{pid}",
                      json={"title": "Low", "priority": "low"}, headers=auth(company_token))
    await client.post(f"/api/v1/tasks/project/{pid}",
                      json={"title": "High", "priority": "high"}, headers=auth(company_token))

    r = await client.get(f"/api/v1/tasks/project/{pid}",
                         params={"priority": "high"}, headers=auth(company_token))
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["title"] == "High"


@pytest.mark.asyncio
async def test_filter_by_assignee(client: AsyncClient, company_token, student_token):
    pid, sid = await _create_project_with_team(client, company_token, student_token)
    await client.post(f"/api/v1/tasks/project/{pid}",
                      json={"title": "Unassigned"}, headers=auth(company_token))
    await client.post(f"/api/v1/tasks/project/{pid}",
                      json={"title": "Mine", "assignee_id": sid}, headers=auth(company_token))

    r = await client.get(f"/api/v1/tasks/project/{pid}",
                         params={"assignee_id": sid}, headers=auth(company_token))
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["title"] == "Mine"


# ── Comments ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_add_and_list_comments(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_with_team(client, company_token, student_token)
    created = await client.post(f"/api/v1/tasks/project/{pid}",
                                json={"title": "Chat here"}, headers=auth(company_token))
    tid = created.json()["id"]

    r = await client.post(f"/api/v1/tasks/{tid}/comments",
                          json={"content": "first!"}, headers=auth(student_token))
    assert r.status_code == 201
    assert r.json()["content"] == "first!"
    assert r.json()["author_username"] == "student1"

    r = await client.get(f"/api/v1/tasks/{tid}/comments", headers=auth(company_token))
    assert r.status_code == 200
    assert len(r.json()) == 1


@pytest.mark.asyncio
async def test_outsider_cant_comment(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_with_team(client, company_token, student_token)
    created = await client.post(f"/api/v1/tasks/project/{pid}",
                                json={"title": "Private"}, headers=auth(company_token))
    tid = created.json()["id"]

    out = await _register_and_verify(client, "o@test.com", "outc", "pass123", "student")
    r = await client.post(f"/api/v1/tasks/{tid}/comments",
                          json={"content": "hi"}, headers=auth(out))
    assert r.status_code == 403
