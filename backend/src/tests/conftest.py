import pytest
import pytest_asyncio
from contextlib import ExitStack
from unittest.mock import AsyncMock, patch, MagicMock
from httpx import AsyncClient, ASGITransport
from tortoise import Tortoise

from src.main import app

TEST_MODELS = [
    "src.users.models",
    "src.skills.models",
    "src.projects.models",
    "src.applications.models",
    "src.reviews.models",
    "src.portfolio.models",
]


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


async def mock_rate_limit_check(key, max_requests=5, window=60):
    return True


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
PATCHES = [
    # Redis core
    ("src.core.redis.cache_get", mock_cache_get),
    ("src.core.redis.cache_set", mock_cache_set),
    ("src.core.redis.cache_delete", mock_cache_delete),
    ("src.core.redis.cache_delete_pattern", mock_cache_delete_pattern),
    ("src.core.redis.blacklist_token", mock_blacklist),
    ("src.core.redis.is_token_blacklisted", mock_is_blacklisted),
    ("src.core.redis.incr_counter", mock_incr_counter),
    ("src.core.redis.get_counter", mock_get_counter),
    ("src.core.redis.reset_counter", mock_reset_counter),
    ("src.core.redis.publish_message", mock_publish_message),
    # Redis at import sites
    ("src.auth.router.rate_limit_check", mock_rate_limit_check),
    ("src.auth.router.cache_set", mock_cache_set),
    ("src.auth.router.cache_get", mock_cache_get),
    ("src.auth.router.cache_delete", mock_cache_delete),
    ("src.auth.service.blacklist_token", mock_blacklist),
    ("src.core.dependencies.is_token_blacklisted", mock_is_blacklisted),
    ("src.users.service.cache_get", mock_cache_get),
    ("src.users.service.cache_set", mock_cache_set),
    ("src.users.service.cache_delete", mock_cache_delete),
    ("src.skills.service.cache_get", mock_cache_get),
    ("src.skills.service.cache_set", mock_cache_set),
    ("src.skills.service.cache_delete", mock_cache_delete),
    ("src.projects.service.cache_delete_pattern", mock_cache_delete_pattern),
    ("src.admin.service.cache_get", mock_cache_get),
    ("src.admin.service.cache_set", mock_cache_set),
    ("src.chat.service.publish_message", mock_publish_message),
    # MongoDB
    ("src.database.mongodb.get_mongodb", mock_get_mongodb),
    ("src.database.mongodb.init_mongodb", mock_init_mongodb),
    ("src.notifications.repository.get_mongodb", mock_get_mongodb),
    ("src.chat.repository.get_mongodb", mock_get_mongodb),
    ("src.admin.repository.get_mongodb", mock_get_mongodb),
    # Notification counters
    ("src.notifications.service.incr_counter", mock_incr_counter),
    ("src.notifications.service.get_counter", mock_get_counter),
    ("src.notifications.service.reset_counter", mock_reset_counter),
    ("src.notifications.service.get_redis", AsyncMock(return_value=MagicMock(decr=AsyncMock()))),
    # Chat Redis
    ("src.chat.router.get_redis", AsyncMock(return_value=MagicMock(pubsub=MagicMock(return_value=MagicMock(
        subscribe=AsyncMock(), unsubscribe=AsyncMock(), close=AsyncMock(),
        listen=MagicMock(return_value=AsyncMock().__aiter__()),
    ))))),
    # Activity logging
    ("src.auth.service.log_activity", AsyncMock()),
    ("src.applications.service.log_activity", AsyncMock()),
    # Email
    ("src.core.email._send_smtp", AsyncMock()),
]


@pytest.fixture(autouse=True)
def patch_externals():
    with ExitStack() as stack:
        for target, mock_obj in PATCHES:
            stack.enter_context(patch(target, mock_obj))
        mock_redis_store.clear()
        mock_mongo.chat_messages = MockCollection()
        mock_mongo.chat_rooms = MockCollection()
        mock_mongo.notifications = MockCollection()
        mock_mongo.activity_logs = MockCollection()
        yield


@pytest_asyncio.fixture(autouse=True)
async def setup_db():
    await Tortoise.init(
        db_url="sqlite://:memory:",
        modules={"models": TEST_MODELS},
    )
    await Tortoise.generate_schemas()
    yield
    await Tortoise.close_connections()


@pytest_asyncio.fixture
async def client():
    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac


async def _register_and_verify(client: AsyncClient, email: str, username: str, password: str, role: str) -> str:
    """Register a user, verify their email, and return an access token."""
    existing_keys = {k for k in mock_redis_store if k.startswith("email_verify:")}
    await client.post("/api/v1/auth/register", json={
        "email": email, "username": username, "password": password, "role": role
    })
    new_keys = {k for k in mock_redis_store if k.startswith("email_verify:")} - existing_keys
    for key in new_keys:
        verify_token = key.split(":", 1)[1]
        await client.get(f"/api/v1/auth/verify-email?token={verify_token}")
    resp = await client.post("/api/v1/auth/login", data={"username": username, "password": password})
    return resp.json()["access_token"]


@pytest_asyncio.fixture
async def student_token(client: AsyncClient):
    return await _register_and_verify(client, "s@test.com", "student1", "pass123", "student")


@pytest_asyncio.fixture
async def company_token(client: AsyncClient):
    return await _register_and_verify(client, "c@test.com", "company1", "pass123", "company")


@pytest_asyncio.fixture
async def admin_token(client: AsyncClient):
    return await _register_and_verify(client, "a@test.com", "admin1", "pass123", "admin")


def auth(token: str):
    return {"Authorization": f"Bearer {token}"}
