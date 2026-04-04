import pytest
from httpx import AsyncClient
from src.tests.conftest import auth, mock_redis_store


@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    r = await client.get("/")
    assert r.status_code == 200
    assert "NexusHub" in r.json()["message"]


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    r = await client.get("/health")
    assert r.status_code == 200


@pytest.mark.asyncio
async def test_register_student(client: AsyncClient):
    r = await client.post("/api/v1/auth/register", json={
        "email": "new@test.com", "username": "newstudent",
        "password": "pass123", "full_name": "New Student", "role": "student"
    })
    assert r.status_code == 201
    assert r.json()["role"] == "student"
    assert r.json()["email"] == "new@test.com"


@pytest.mark.asyncio
async def test_register_company(client: AsyncClient):
    r = await client.post("/api/v1/auth/register", json={
        "email": "co@test.com", "username": "newcompany",
        "password": "pass123", "role": "company"
    })
    assert r.status_code == 201
    assert r.json()["role"] == "company"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "dup@test.com", "username": "user1dup", "password": "pass123", "role": "student"
    })
    r = await client.post("/api/v1/auth/register", json={
        "email": "dup@test.com", "username": "user2dup", "password": "pass123", "role": "student"
    })
    assert r.status_code == 400


@pytest.mark.asyncio
async def test_register_duplicate_username(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "a1@test.com", "username": "sameuser", "password": "pass123", "role": "student"
    })
    r = await client.post("/api/v1/auth/register", json={
        "email": "a2@test.com", "username": "sameuser", "password": "pass123", "role": "student"
    })
    assert r.status_code == 400


async def _find_and_verify(client: AsyncClient):
    """Helper: find a verification token in mock store and call verify endpoint."""
    for key in list(mock_redis_store):
        if key.startswith("email_verify:"):
            token = key.split(":", 1)[1]
            await client.get(f"/api/v1/auth/verify-email?token={token}")
            return


@pytest.mark.asyncio
async def test_login_success(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "login@test.com", "username": "loginuser", "password": "pass123", "role": "student"
    })
    await _find_and_verify(client)
    r = await client.post("/api/v1/auth/login", data={"username": "loginuser", "password": "pass123"})
    assert r.status_code == 200
    assert "access_token" in r.json()
    assert "refresh_token" in r.json()


@pytest.mark.asyncio
async def test_login_invalid(client: AsyncClient):
    r = await client.post("/api/v1/auth/login", data={"username": "nobody", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_wrong_password(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "wp@test.com", "username": "wpuser", "password": "pass123", "role": "student"
    })
    r = await client.post("/api/v1/auth/login", data={"username": "wpuser", "password": "wrong"})
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient, student_token: str):
    r = await client.get("/api/v1/auth/me", headers=auth(student_token))
    assert r.status_code == 200
    assert r.json()["username"] == "student1"


@pytest.mark.asyncio
async def test_get_me_no_token(client: AsyncClient):
    r = await client.get("/api/v1/auth/me")
    assert r.status_code == 401


@pytest.mark.asyncio
async def test_login_unverified(client: AsyncClient):
    """Login should fail if email is not verified."""
    await client.post("/api/v1/auth/register", json={
        "email": "unverified@test.com", "username": "unverified", "password": "pass123", "role": "student"
    })
    r = await client.post("/api/v1/auth/login", data={"username": "unverified", "password": "pass123"})
    assert r.status_code == 403
    assert "not verified" in r.json()["detail"].lower()


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "ref@test.com", "username": "refuser", "password": "pass123", "role": "student"
    })
    await _find_and_verify(client)
    login = await client.post("/api/v1/auth/login", data={"username": "refuser", "password": "pass123"})
    refresh = login.json()["refresh_token"]
    r = await client.post("/api/v1/auth/refresh", json={"refresh_token": refresh})
    assert r.status_code == 200
    assert "access_token" in r.json()


@pytest.mark.asyncio
async def test_logout(client: AsyncClient, student_token: str):
    r = await client.post("/api/v1/auth/logout", headers=auth(student_token))
    assert r.status_code == 204


@pytest.mark.asyncio
async def test_register_short_password(client: AsyncClient):
    r = await client.post("/api/v1/auth/register", json={
        "email": "sp@test.com", "username": "spuser", "password": "12", "role": "student"
    })
    assert r.status_code == 422
