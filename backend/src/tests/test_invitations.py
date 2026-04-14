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


@pytest.mark.asyncio
async def test_company_cannot_accept_invite(
    client: AsyncClient, company_token: str, student_token: str
):
    """Owner can withdraw (reject) an invite but cannot accept on the student's behalf."""
    _, _, _, app_id = await _seed_invite(client, company_token, student_token)

    r = await client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "accepted"}, headers=auth(company_token),
    )
    assert r.status_code == 403
    assert "student" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_admin_can_accept_invite_on_behalf(
    client: AsyncClient, company_token: str, student_token: str, admin_token: str
):
    """Admin override: admin can accept an invite on the student's behalf."""
    _, _, _, app_id = await _seed_invite(client, company_token, student_token)

    r = await client.put(
        f"/api/v1/applications/{app_id}/status",
        json={"status": "accepted"}, headers=auth(admin_token),
    )
    assert r.status_code == 200
    assert r.json()["status"] == "accepted"
