import pytest
from httpx import AsyncClient
from src.tests.conftest import auth


# ── Users Tests ──────────────────────────────────────

@pytest.mark.asyncio
async def test_get_user(client: AsyncClient, student_token: str):
    me = await client.get("/api/v1/auth/me", headers=auth(student_token))
    user_id = me.json()["id"]
    r = await client.get(f"/api/v1/users/{user_id}")
    assert r.status_code == 200
    assert r.json()["username"] == "student1"


@pytest.mark.asyncio
async def test_get_user_not_found(client: AsyncClient):
    r = await client.get("/api/v1/users/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_user(client: AsyncClient, student_token: str):
    me = await client.get("/api/v1/auth/me", headers=auth(student_token))
    uid = me.json()["id"]
    r = await client.put(f"/api/v1/users/{uid}", json={"full_name": "Updated Name", "bio": "My bio"},
                         headers=auth(student_token))
    assert r.status_code == 200
    assert r.json()["full_name"] == "Updated Name"
    assert r.json()["bio"] == "My bio"


@pytest.mark.asyncio
async def test_update_user_unauthorized(client: AsyncClient, student_token: str):
    r = await client.put("/api/v1/users/9999", json={"full_name": "Hack"}, headers=auth(student_token))
    assert r.status_code in (403, 404)


# ── Skills Tests ─────────────────────────────────────

@pytest.mark.asyncio
async def test_create_skill(client: AsyncClient, student_token: str):
    r = await client.post("/api/v1/skills/", json={"name": "Python", "category": "Programming"},
                          headers=auth(student_token))
    assert r.status_code == 201
    assert r.json()["name"] == "Python"


@pytest.mark.asyncio
async def test_create_duplicate_skill(client: AsyncClient, student_token: str):
    await client.post("/api/v1/skills/", json={"name": "Java"}, headers=auth(student_token))
    r = await client.post("/api/v1/skills/", json={"name": "Java"}, headers=auth(student_token))
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_list_skills(client: AsyncClient, student_token: str):
    await client.post("/api/v1/skills/", json={"name": "Go"}, headers=auth(student_token))
    r = await client.get("/api/v1/skills/")
    assert r.status_code == 200
    assert len(r.json()) >= 1


@pytest.mark.asyncio
async def test_add_skill_to_user(client: AsyncClient, student_token: str):
    skill = await client.post("/api/v1/skills/", json={"name": "Rust"}, headers=auth(student_token))
    me = await client.get("/api/v1/auth/me", headers=auth(student_token))
    uid = me.json()["id"]
    sid = skill.json()["id"]
    r = await client.post(f"/api/v1/users/{uid}/skills/{sid}", headers=auth(student_token))
    assert r.status_code == 204


# ── Projects Tests ───────────────────────────────────

@pytest.mark.asyncio
async def test_create_project_company(client: AsyncClient, company_token: str):
    r = await client.post("/api/v1/projects/", json={
        "title": "Test Project", "description": "A detailed description here",
        "max_participants": 3,
    }, headers=auth(company_token))
    assert r.status_code == 201
    assert r.json()["title"] == "Test Project"
    assert r.json()["status"] == "open"


@pytest.mark.asyncio
async def test_create_student_project(client: AsyncClient, student_token: str):
    r = await client.post("/api/v1/projects/", json={
        "title": "Student Collab", "description": "Looking for help on my project",
        "is_student_project": True,
    }, headers=auth(student_token))
    assert r.status_code == 201
    assert r.json()["is_student_project"] is True


@pytest.mark.asyncio
async def test_student_cant_create_company_project(client: AsyncClient, student_token: str):
    r = await client.post("/api/v1/projects/", json={
        "title": "Should Fail", "description": "Students cant create company projects",
    }, headers=auth(student_token))
    assert r.status_code == 403


@pytest.mark.asyncio
async def test_list_projects(client: AsyncClient, company_token: str):
    await client.post("/api/v1/projects/", json={
        "title": "P1", "description": "Description one here"
    }, headers=auth(company_token))
    r = await client.get("/api/v1/projects/")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


@pytest.mark.asyncio
async def test_list_projects_with_search(client: AsyncClient, company_token: str):
    await client.post("/api/v1/projects/", json={
        "title": "Machine Learning Pipeline", "description": "Build an ML pipeline"
    }, headers=auth(company_token))
    r = await client.get("/api/v1/projects/?search=Machine")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_get_project(client: AsyncClient, company_token: str):
    created = await client.post("/api/v1/projects/", json={
        "title": "Get Me", "description": "Project to retrieve later"
    }, headers=auth(company_token))
    pid = created.json()["id"]
    r = await client.get(f"/api/v1/projects/{pid}")
    assert r.status_code == 200
    assert r.json()["title"] == "Get Me"


@pytest.mark.asyncio
async def test_get_project_not_found(client: AsyncClient):
    r = await client.get("/api/v1/projects/9999")
    assert r.status_code == 404


@pytest.mark.asyncio
async def test_update_project(client: AsyncClient, company_token: str):
    created = await client.post("/api/v1/projects/", json={
        "title": "Update Me", "description": "Will be updated"
    }, headers=auth(company_token))
    pid = created.json()["id"]
    r = await client.put(f"/api/v1/projects/{pid}", json={"title": "Updated Title"},
                         headers=auth(company_token))
    assert r.status_code == 200
    assert r.json()["title"] == "Updated Title"


@pytest.mark.asyncio
async def test_delete_project(client: AsyncClient, company_token: str):
    created = await client.post("/api/v1/projects/", json={
        "title": "Delete Me", "description": "Will be deleted"
    }, headers=auth(company_token))
    pid = created.json()["id"]
    r = await client.delete(f"/api/v1/projects/{pid}", headers=auth(company_token))
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_update_project_unauthorized(client: AsyncClient, company_token: str, student_token: str):
    created = await client.post("/api/v1/projects/", json={
        "title": "Not Yours", "description": "Someone else's project"
    }, headers=auth(company_token))
    pid = created.json()["id"]
    r = await client.put(f"/api/v1/projects/{pid}", json={"title": "Hacked"},
                         headers=auth(student_token))
    assert r.status_code == 403
