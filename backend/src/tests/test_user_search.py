import pytest
from httpx import AsyncClient
from src.tests.conftest import auth, _register_and_verify
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
    _, s2_id = await _create_student(client, "s2@test.com", "student2")

    py = await Skill.create(name="Python", category="language")
    docker = await Skill.create(name="Docker", category="tool")

    me_r = await client.get("/api/v1/auth/me", headers=auth(student_token))
    s1 = await User.filter(id=me_r.json()["id"]).first()
    await s1.skills.add(py)
    await s1.skills.add(docker)

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
    proj = await client.post("/api/v1/projects/", json={
        "title": "Busy work", "description": "description long enough"
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
