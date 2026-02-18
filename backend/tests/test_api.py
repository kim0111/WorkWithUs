import pytest
import pytest_asyncio
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from app.main import app
from app.database.session import Base, get_db

# Use SQLite for tests
TEST_DATABASE_URL = "sqlite+aiosqlite:///./test.db"
test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


app.dependency_overrides[get_db] = override_get_db


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
    yield
    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


# ── Tests ────────────────────────────────────────────

@pytest.mark.asyncio
async def test_root(client: AsyncClient):
    response = await client.get("/")
    assert response.status_code == 200
    assert "message" in response.json()


@pytest.mark.asyncio
async def test_health(client: AsyncClient):
    response = await client.get("/health")
    assert response.status_code == 200
    assert response.json()["status"] == "ok"


@pytest.mark.asyncio
async def test_register_student(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "student@test.com",
        "username": "teststudent",
        "password": "password123",
        "full_name": "Test Student",
        "role": "student",
    })
    assert response.status_code == 201
    data = response.json()
    assert data["email"] == "student@test.com"
    assert data["role"] == "student"


@pytest.mark.asyncio
async def test_register_company(client: AsyncClient):
    response = await client.post("/api/v1/auth/register", json={
        "email": "company@test.com",
        "username": "testcompany",
        "password": "password123",
        "full_name": "Test Company",
        "role": "company",
    })
    assert response.status_code == 201
    assert response.json()["role"] == "company"


@pytest.mark.asyncio
async def test_register_duplicate_email(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "dup@test.com",
        "username": "user1",
        "password": "password123",
        "role": "student",
    })
    response = await client.post("/api/v1/auth/register", json={
        "email": "dup@test.com",
        "username": "user2",
        "password": "password123",
        "role": "student",
    })
    assert response.status_code == 400


@pytest.mark.asyncio
async def test_login(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "login@test.com",
        "username": "loginuser",
        "password": "password123",
        "role": "student",
    })
    response = await client.post("/api/v1/auth/login", json={
        "username": "loginuser",
        "password": "password123",
    })
    assert response.status_code == 200
    data = response.json()
    assert "access_token" in data
    assert "refresh_token" in data


@pytest.mark.asyncio
async def test_login_invalid(client: AsyncClient):
    response = await client.post("/api/v1/auth/login", json={
        "username": "nonexistent",
        "password": "wrong",
    })
    assert response.status_code == 401


@pytest.mark.asyncio
async def test_get_me(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "me@test.com",
        "username": "meuser",
        "password": "password123",
        "role": "student",
    })
    login = await client.post("/api/v1/auth/login", json={
        "username": "meuser",
        "password": "password123",
    })
    token = login.json()["access_token"]

    response = await client.get("/api/v1/auth/me", headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 200
    assert response.json()["username"] == "meuser"


@pytest.mark.asyncio
async def test_create_project_as_company(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "proj@test.com",
        "username": "projcompany",
        "password": "password123",
        "role": "company",
    })
    login = await client.post("/api/v1/auth/login", json={
        "username": "projcompany",
        "password": "password123",
    })
    token = login.json()["access_token"]

    response = await client.post("/api/v1/projects/", json={
        "title": "Test Project",
        "description": "A test project description here",
        "max_participants": 3,
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201
    assert response.json()["title"] == "Test Project"


@pytest.mark.asyncio
async def test_get_projects(client: AsyncClient):
    response = await client.get("/api/v1/projects/")
    assert response.status_code == 200
    assert "items" in response.json()
    assert "total" in response.json()


@pytest.mark.asyncio
async def test_create_skill(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "skill@test.com",
        "username": "skilluser",
        "password": "password123",
        "role": "student",
    })
    login = await client.post("/api/v1/auth/login", json={
        "username": "skilluser",
        "password": "password123",
    })
    token = login.json()["access_token"]

    response = await client.post("/api/v1/skills/", json={
        "name": "Python",
        "category": "Programming",
    }, headers={"Authorization": f"Bearer {token}"})
    assert response.status_code == 201


@pytest.mark.asyncio
async def test_get_skills(client: AsyncClient):
    response = await client.get("/api/v1/skills/")
    assert response.status_code == 200


@pytest.mark.asyncio
async def test_refresh_token(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "refresh@test.com",
        "username": "refreshuser",
        "password": "password123",
        "role": "student",
    })
    login = await client.post("/api/v1/auth/login", json={
        "username": "refreshuser",
        "password": "password123",
    })
    refresh = login.json()["refresh_token"]

    response = await client.post("/api/v1/auth/refresh", json={
        "refresh_token": refresh,
    })
    assert response.status_code == 200
    assert "access_token" in response.json()
