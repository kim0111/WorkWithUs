import pytest
from httpx import AsyncClient
from src.tests.conftest import auth, _register_and_verify


# ── Helper ──────────────────────────────────────────────

async def _create_project_and_accept(client, company_token, student_token, title="Team Project"):
    """Create project, apply, accept — returns (project_id, application_id)."""
    proj = await client.post("/api/v1/projects/", json={
        "title": title, "description": "Project for team testing", "max_participants": 5,
    }, headers=auth(company_token))
    pid = proj.json()["id"]

    app = await client.post("/api/v1/applications/", json={
        "project_id": pid, "cover_letter": "I want in",
    }, headers=auth(student_token))
    aid = app.json()["id"]

    await client.put(f"/api/v1/applications/{aid}/status",
                     json={"status": "accepted"}, headers=auth(company_token))
    return pid, aid


# ── Auto-add on accept ─────────────────────────────────

@pytest.mark.asyncio
async def test_accept_creates_team_member(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_and_accept(client, company_token, student_token)

    r = await client.get(f"/api/v1/teams/project/{pid}", headers=auth(company_token))
    assert r.status_code == 200
    members = r.json()
    assert len(members) == 1
    assert members[0]["username"] == "student1"
    assert members[0]["is_lead"] is True  # first accepted becomes lead


@pytest.mark.asyncio
async def test_second_accepted_is_not_lead(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_and_accept(client, company_token, student_token)

    # Register second student and apply
    s2_token = await _register_and_verify(client, "s2@test.com", "student2", "pass123", "student")
    app2 = await client.post("/api/v1/applications/", json={
        "project_id": pid, "cover_letter": "Me too",
    }, headers=auth(s2_token))
    aid2 = app2.json()["id"]
    await client.put(f"/api/v1/applications/{aid2}/status",
                     json={"status": "accepted"}, headers=auth(company_token))

    r = await client.get(f"/api/v1/teams/project/{pid}", headers=auth(company_token))
    members = r.json()
    assert len(members) == 2
    leads = [m for m in members if m["is_lead"]]
    non_leads = [m for m in members if not m["is_lead"]]
    assert len(leads) == 1
    assert len(non_leads) == 1


# ── Manual add/remove ──────────────────────────────────

@pytest.mark.asyncio
async def test_owner_adds_member(client: AsyncClient, company_token, student_token):
    proj = await client.post("/api/v1/projects/", json={
        "title": "Manual Add", "description": "Owner adds manually", "max_participants": 5,
    }, headers=auth(company_token))
    pid = proj.json()["id"]

    from src.users.models import User
    student = await User.filter(username="student1").first()

    r = await client.post(f"/api/v1/teams/project/{pid}/members", json={
        "user_id": student.id, "role": "frontend",
    }, headers=auth(company_token))
    assert r.status_code == 201
    assert r.json()["role"] == "frontend"


@pytest.mark.asyncio
async def test_remove_member(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_and_accept(client, company_token, student_token)

    from src.users.models import User
    student = await User.filter(username="student1").first()

    r = await client.delete(f"/api/v1/teams/project/{pid}/members/{student.id}",
                            headers=auth(company_token))
    assert r.status_code == 204

    r = await client.get(f"/api/v1/teams/project/{pid}", headers=auth(company_token))
    assert len(r.json()) == 0


@pytest.mark.asyncio
async def test_duplicate_add_fails(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_and_accept(client, company_token, student_token)

    from src.users.models import User
    student = await User.filter(username="student1").first()

    r = await client.post(f"/api/v1/teams/project/{pid}/members", json={
        "user_id": student.id, "role": "backend",
    }, headers=auth(company_token))
    assert r.status_code == 400


# ── Update member role ─────────────────────────────────

@pytest.mark.asyncio
async def test_update_member_role(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_and_accept(client, company_token, student_token)

    from src.users.models import User
    student = await User.filter(username="student1").first()

    r = await client.put(f"/api/v1/teams/project/{pid}/members/{student.id}", json={
        "role": "backend",
    }, headers=auth(company_token))
    assert r.status_code == 200
    assert r.json()["role"] == "backend"


# ── My teams ───────────────────────────────────────────

@pytest.mark.asyncio
async def test_my_teams(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_and_accept(client, company_token, student_token)

    r = await client.get("/api/v1/teams/my", headers=auth(student_token))
    assert r.status_code == 200
    assert len(r.json()) == 1
    assert r.json()[0]["project_id"] == pid


# ── Authorization ──────────────────────────────────────

@pytest.mark.asyncio
async def test_student_cant_add_member(client: AsyncClient, company_token, student_token):
    proj = await client.post("/api/v1/projects/", json={
        "title": "Auth Test", "description": "Student shouldn't add", "max_participants": 5,
    }, headers=auth(company_token))
    pid = proj.json()["id"]

    s2_token = await _register_and_verify(client, "s3@test.com", "student3", "pass123", "student")
    from src.users.models import User
    s2 = await User.filter(username="student3").first()

    r = await client.post(f"/api/v1/teams/project/{pid}/members", json={
        "user_id": s2.id, "role": "other",
    }, headers=auth(student_token))
    assert r.status_code == 403


# ── Max participants ───────────────────────────────────

@pytest.mark.asyncio
async def test_max_participants_enforced(client: AsyncClient, company_token, student_token):
    proj = await client.post("/api/v1/projects/", json={
        "title": "Max1", "description": "Only one participant", "max_participants": 1,
    }, headers=auth(company_token))
    pid = proj.json()["id"]

    app = await client.post("/api/v1/applications/", json={"project_id": pid},
                            headers=auth(student_token))
    aid = app.json()["id"]
    await client.put(f"/api/v1/applications/{aid}/status",
                     json={"status": "accepted"}, headers=auth(company_token))

    s2_token = await _register_and_verify(client, "s4@test.com", "student4", "pass123", "student")
    from src.users.models import User
    s2 = await User.filter(username="student4").first()

    r = await client.post(f"/api/v1/teams/project/{pid}/members", json={
        "user_id": s2.id, "role": "other",
    }, headers=auth(company_token))
    assert r.status_code == 400
    assert "maximum" in r.json()["detail"].lower()


# ── Team chat ──────────────────────────────────────────

@pytest.mark.asyncio
async def test_team_chat_room(client: AsyncClient, company_token, student_token):
    pid, _ = await _create_project_and_accept(client, company_token, student_token)

    r = await client.post(f"/api/v1/chat/team-room/{pid}", headers=auth(company_token))
    assert r.status_code == 200
    room = r.json()
    assert room["project_id"] == pid
    assert len(room["participants"]) >= 2  # owner + student
