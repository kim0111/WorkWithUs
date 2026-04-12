import pytest
from httpx import AsyncClient
from src.tests.conftest import auth


async def _create_project(client, company_token, title="Demo Project"):
    r = await client.post("/api/v1/projects/", json={
        "title": title, "description": "A demo project for history tests",
    }, headers=auth(company_token))
    assert r.status_code == 201
    return r.json()["id"]


@pytest.mark.asyncio
async def test_create_application_initializes_history(
    client: AsyncClient, company_token: str, student_token: str
):
    """Applying should seed status_history with exactly one 'pending' entry by the applicant."""
    project_id = await _create_project(client, company_token)

    r = await client.post("/api/v1/applications/", json={
        "project_id": project_id, "cover_letter": "please pick me",
    }, headers=auth(student_token))
    assert r.status_code == 201
    body = r.json()

    assert "status_history" in body
    assert len(body["status_history"]) == 1
    entry = body["status_history"][0]
    assert entry["status"] == "pending"
    assert entry["actor_id"] is not None
    assert entry["actor_name"]  # non-empty
    assert entry["note"] is None


@pytest.mark.asyncio
async def test_status_transition_appends_history(
    client: AsyncClient, company_token: str, student_token: str
):
    """Each transition should append one new entry with the correct actor."""
    project_id = await _create_project(client, company_token)

    company_me_r = await client.get("/api/v1/auth/me", headers=auth(company_token))
    company_user_id = company_me_r.json()["id"]
    student_me_r = await client.get("/api/v1/auth/me", headers=auth(student_token))
    student_user_id = student_me_r.json()["id"]

    apply_r = await client.post("/api/v1/applications/", json={
        "project_id": project_id,
    }, headers=auth(student_token))
    app_id = apply_r.json()["id"]

    # Company accepts
    accept_r = await client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "accepted"}, headers=auth(company_token),
    )
    assert accept_r.status_code == 200
    body = accept_r.json()
    assert len(body["status_history"]) == 2
    assert body["status_history"][1]["status"] == "accepted"
    assert body["status_history"][1]["note"] is None
    assert body["status_history"][1]["actor_id"] == company_user_id

    # Student starts working
    start_r = await client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "in_progress"}, headers=auth(student_token),
    )
    assert start_r.status_code == 200
    body = start_r.json()
    assert len(body["status_history"]) == 3
    assert body["status_history"][2]["status"] == "in_progress"
    assert body["status_history"][2]["actor_id"] == student_user_id


@pytest.mark.asyncio
async def test_submission_note_captured_in_history(
    client: AsyncClient, company_token: str, student_token: str
):
    """submission_note and revision_note should be captured per-transition in history."""
    project_id = await _create_project(client, company_token)

    apply_r = await client.post("/api/v1/applications/", json={
        "project_id": project_id,
    }, headers=auth(student_token))
    app_id = apply_r.json()["id"]

    await client.put(f"/api/v1/applications/{app_id}/status",
                     json={"status": "accepted"}, headers=auth(company_token))
    await client.put(f"/api/v1/applications/{app_id}/status",
                     json={"status": "in_progress"}, headers=auth(student_token))

    # Submit with a note
    submit_r = await client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "submitted", "note": "v1 ready for review"},
        headers=auth(student_token),
    )
    assert submit_r.status_code == 200
    body = submit_r.json()
    submitted_entry = body["status_history"][-1]
    assert submitted_entry["status"] == "submitted"
    assert submitted_entry["note"] == "v1 ready for review"

    # Request revision with a note
    rev_r = await client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "revision_requested", "note": "fix the README"},
        headers=auth(company_token),
    )
    assert rev_r.status_code == 200
    body = rev_r.json()
    rev_entry = body["status_history"][-1]
    assert rev_entry["status"] == "revision_requested"
    assert rev_entry["note"] == "fix the README"
