import asyncio
import pytest
import pytest_asyncio
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker

from src.main import app
from src.database.postgres import Base, get_db

TEST_DB = "sqlite+aiosqlite:///./test.db"
test_engine = create_async_engine(TEST_DB, echo=False)
TestSession = async_sessionmaker(test_engine, class_=AsyncSession, expire_on_commit=False)


async def override_get_db():
    async with TestSession() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise


# Mock Redis
mock_redis_store = {}


async def mock_cache_get(key):
    return mock_redis_store.get(key)


async def mock_cache_set(key, value, ttl=None):
    mock_redis_store[key] = value


async def mock_cache_delete(key):
    mock_redis_store.pop(key, None)


async def mock_cache_delete_pattern(pattern):
    prefix = pattern.replace("*", "")
    keys = [k for k in mock_redis_store if k.startswith(prefix)]
    for k in keys:
        mock_redis_store.pop(k, None)


async def mock_blacklist(*a, **kw):
    pass


async def mock_is_blacklisted(token):
    return False


async def mock_incr_counter(key):
    return 1


async def mock_get_counter(key):
    return 0


async def mock_reset_counter(key):
    pass


async def mock_publish_message(channel, data):
    pass


# Mock MongoDB
class MockCollection:
    def __init__(self):
        self.docs = []
        self._counter = 0

    async def insert_one(self, doc):
        self._counter += 1
        from bson import ObjectId
        doc["_id"] = ObjectId()
        self.docs.append(doc)
        return MagicMock(inserted_id=doc["_id"])

    async def find_one(self, *a, **kw):
        return self.docs[0] if self.docs else None

    async def find_one_and_update(self, *a, **kw):
        return self.docs[0] if self.docs else None

    async def update_one(self, *a, **kw):
        pass

    async def update_many(self, *a, **kw):
        pass

    async def count_documents(self, query):
        return len(self.docs)

    def find(self, *a, **kw):
        return MockCursor(self.docs)

    async def create_index(self, *a, **kw):
        pass


class MockCursor:
    def __init__(self, docs):
        self._docs = docs
        self._skip = 0
        self._limit = 100

    def sort(self, *a, **kw):
        return self

    def skip(self, n):
        self._skip = n
        return self

    def limit(self, n):
        self._limit = n
        return self

    def __aiter__(self):
        self._iter = iter(self._docs[self._skip:self._skip + self._limit])
        return self

    async def __anext__(self):
        try:
            return next(self._iter)
        except StopIteration:
            raise StopAsyncIteration


class MockMongoDB:
    def __init__(self):
        self.chat_messages = MockCollection()
        self.chat_rooms = MockCollection()
        self.notifications = MockCollection()
        self.activity_logs = MockCollection()


mock_mongo = MockMongoDB()


async def mock_get_mongodb():
    return mock_mongo


async def mock_init_mongodb():
    pass


# Apply all patches
@pytest.fixture(autouse=True)
def patch_externals():
    with patch("app.core.redis.cache_get", mock_cache_get), \
         patch("app.core.redis.cache_set", mock_cache_set), \
         patch("app.core.redis.cache_delete", mock_cache_delete), \
         patch("app.core.redis.cache_delete_pattern", mock_cache_delete_pattern), \
         patch("app.core.redis.blacklist_token", mock_blacklist), \
         patch("app.core.redis.is_token_blacklisted", mock_is_blacklisted), \
         patch("app.core.redis.incr_counter", mock_incr_counter), \
         patch("app.core.redis.get_counter", mock_get_counter), \
         patch("app.core.redis.reset_counter", mock_reset_counter), \
         patch("app.core.redis.publish_message", mock_publish_message), \
         patch("app.database.mongodb.get_mongodb", mock_get_mongodb), \
         patch("app.database.mongodb.init_mongodb", mock_init_mongodb), \
         patch("app.notifications.router.get_mongodb", mock_get_mongodb), \
         patch("app.chat.router.get_mongodb", mock_get_mongodb), \
         patch("app.admin.router.get_mongodb", mock_get_mongodb), \
         patch("app.notifications.router.incr_counter", mock_incr_counter), \
         patch("app.notifications.router.get_counter", mock_get_counter), \
         patch("app.notifications.router.reset_counter", mock_reset_counter), \
         patch("app.core.email._send_smtp", MagicMock()):
        mock_redis_store.clear()
        mock_mongo.chat_messages = MockCollection()
        mock_mongo.chat_rooms = MockCollection()
        mock_mongo.notifications = MockCollection()
        mock_mongo.activity_logs = MockCollection()
        yield


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


@pytest_asyncio.fixture
async def student_token(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "s@test.com", "username": "student1", "password": "pass123", "role": "student"
    })
    resp = await client.post("/api/v1/auth/login", json={"username": "student1", "password": "pass123"})
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def company_token(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "c@test.com", "username": "company1", "password": "pass123", "role": "company"
    })
    resp = await client.post("/api/v1/auth/login", json={"username": "company1", "password": "pass123"})
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient):
    await client.post("/api/v1/auth/register", json={
        "email": "a@test.com", "username": "admin1", "password": "pass123", "role": "admin"
    })
    resp = await client.post("/api/v1/auth/login", json={"username": "admin1", "password": "pass123"})
    return resp.json()["access_token"]


def auth(token: str):
    return {"Authorization": f"Bearer {token}"}
