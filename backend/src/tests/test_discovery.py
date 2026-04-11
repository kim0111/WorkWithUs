import pytest
from httpx import AsyncClient
from src.tests.conftest import auth


@pytest.mark.asyncio
async def test_search_matches_description(client: AsyncClient, company_token: str):
    """Search should match project description, not just title."""
    await client.post("/api/v1/projects/", json={
        "title": "Generic Title", "description": "Build a machine learning pipeline"
    }, headers=auth(company_token))

    r = await client.get("/api/v1/projects/?search=machine+learning")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
    assert any("machine learning" in p["description"].lower() for p in r.json()["items"])


@pytest.mark.asyncio
async def test_search_matches_skill_name(client: AsyncClient, company_token: str, student_token: str):
    """Search should match required skill names."""
    skill_resp = await client.post("/api/v1/skills/", json={
        "name": "TensorFlow", "category": "ML"
    }, headers=auth(student_token))
    skill_id = skill_resp.json()["id"]

    await client.post("/api/v1/projects/", json={
        "title": "Data Project", "description": "A data project",
        "skill_ids": [skill_id],
    }, headers=auth(company_token))

    r = await client.get("/api/v1/projects/?search=TensorFlow")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


@pytest.mark.asyncio
async def test_filter_by_skill_ids(client: AsyncClient, company_token: str, student_token: str):
    """skill_ids param should filter to projects with matching skills."""
    s1 = await client.post("/api/v1/skills/", json={"name": "React"}, headers=auth(student_token))
    s2 = await client.post("/api/v1/skills/", json={"name": "Django"}, headers=auth(student_token))
    sid1, sid2 = s1.json()["id"], s2.json()["id"]

    await client.post("/api/v1/projects/", json={
        "title": "React App", "description": "Frontend application",
        "skill_ids": [sid1],
    }, headers=auth(company_token))

    await client.post("/api/v1/projects/", json={
        "title": "Django API", "description": "Backend application",
        "skill_ids": [sid2],
    }, headers=auth(company_token))

    # Filter by React only
    r = await client.get(f"/api/v1/projects/?skill_ids={sid1}")
    assert r.status_code == 200
    titles = [p["title"] for p in r.json()["items"]]
    assert "React App" in titles
    assert "Django API" not in titles

    # Filter by both (OR logic)
    r = await client.get(f"/api/v1/projects/?skill_ids={sid1}&skill_ids={sid2}")
    assert r.status_code == 200
    assert r.json()["total"] >= 2


@pytest.mark.asyncio
async def test_sort_by_deadline(client: AsyncClient, company_token: str):
    """sort=deadline should order by deadline ascending, nulls last."""
    await client.post("/api/v1/projects/", json={
        "title": "No Deadline", "description": "Project without deadline",
    }, headers=auth(company_token))

    await client.post("/api/v1/projects/", json={
        "title": "Soon Deadline", "description": "Project with near deadline",
        "deadline": "2026-05-01T00:00:00",
    }, headers=auth(company_token))

    await client.post("/api/v1/projects/", json={
        "title": "Late Deadline", "description": "Project with later deadline",
        "deadline": "2026-12-01T00:00:00",
    }, headers=auth(company_token))

    r = await client.get("/api/v1/projects/?sort=deadline")
    assert r.status_code == 200
    items = r.json()["items"]
    deadlined = [p for p in items if p["deadline"] is not None]
    assert len(deadlined) >= 2
    assert deadlined[0]["title"] == "Soon Deadline"
    assert deadlined[1]["title"] == "Late Deadline"


@pytest.mark.asyncio
async def test_sort_newest_is_default(client: AsyncClient, company_token: str):
    """Default sort (newest) should return most recent first."""
    await client.post("/api/v1/projects/", json={
        "title": "First Created", "description": "Created first in time",
    }, headers=auth(company_token))
    await client.post("/api/v1/projects/", json={
        "title": "Second Created", "description": "Created second in time",
    }, headers=auth(company_token))

    r = await client.get("/api/v1/projects/")
    assert r.status_code == 200
    items = r.json()["items"]
    assert items[0]["title"] == "Second Created"


@pytest.mark.asyncio
async def test_combined_filters(client: AsyncClient, company_token: str, student_token: str):
    """skill_ids + search + status should all work together."""
    skill = await client.post("/api/v1/skills/", json={"name": "Kotlin"}, headers=auth(student_token))
    sid = skill.json()["id"]

    await client.post("/api/v1/projects/", json={
        "title": "Android App", "description": "Mobile development project",
        "skill_ids": [sid],
    }, headers=auth(company_token))

    r = await client.get(f"/api/v1/projects/?skill_ids={sid}&search=mobile&status=open")
    assert r.status_code == 200
    assert r.json()["total"] >= 1


@pytest.mark.asyncio
async def test_existing_search_still_works(client: AsyncClient, company_token: str):
    """Title search (existing behavior) must not break."""
    await client.post("/api/v1/projects/", json={
        "title": "Unique Title XYZ", "description": "Some description",
    }, headers=auth(company_token))

    r = await client.get("/api/v1/projects/?search=Unique+Title")
    assert r.status_code == 200
    assert r.json()["total"] >= 1
