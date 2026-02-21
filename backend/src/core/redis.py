import json
from typing import Optional, Any
import redis.asyncio as aioredis
from src.core.config import settings

_redis: Optional[aioredis.Redis] = None


async def get_redis() -> aioredis.Redis:
    global _redis
    if _redis is None:
        _redis = aioredis.from_url(settings.REDIS_URL, decode_responses=True)
    return _redis


async def close_redis():
    global _redis
    if _redis:
        await _redis.close()
        _redis = None


# ── Cache helpers ────────────────────────────────────

async def cache_get(key: str) -> Optional[Any]:
    r = await get_redis()
    val = await r.get(key)
    if val:
        try:
            return json.loads(val)
        except (json.JSONDecodeError, TypeError):
            return val
    return None


async def cache_set(key: str, value: Any, ttl: int = None):
    r = await get_redis()
    ttl = ttl or settings.CACHE_TTL
    if isinstance(value, (dict, list)):
        value = json.dumps(value, default=str)
    await r.set(key, value, ex=ttl)


async def cache_delete(key: str):
    r = await get_redis()
    await r.delete(key)


async def cache_delete_pattern(pattern: str):
    r = await get_redis()
    keys = []
    async for key in r.scan_iter(match=pattern):
        keys.append(key)
    if keys:
        await r.delete(*keys)


# ── JWT Blacklist ────────────────────────────────────

async def blacklist_token(token: str, ttl: int):
    r = await get_redis()
    await r.set(f"bl:{token}", "1", ex=ttl)


async def is_token_blacklisted(token: str) -> bool:
    r = await get_redis()
    return await r.exists(f"bl:{token}") > 0


# ── Pub/Sub for WebSocket chat ───────────────────────

async def publish_message(channel: str, data: dict):
    r = await get_redis()
    await r.publish(channel, json.dumps(data, default=str))


def get_pubsub():
    """Returns a pubsub instance — caller must subscribe and listen."""
    import asyncio
    async def _get():
        r = await get_redis()
        return r.pubsub()
    return asyncio.ensure_future(_get())


# ── Rate limiting ────────────────────────────────────

async def rate_limit_check(key: str, max_requests: int, window: int) -> bool:
    r = await get_redis()
    current = await r.incr(key)
    if current == 1:
        await r.expire(key, window)
    return current <= max_requests


# ── Counters (e.g. unread notifications) ─────────────

async def incr_counter(key: str) -> int:
    r = await get_redis()
    return await r.incr(key)


async def get_counter(key: str) -> int:
    r = await get_redis()
    val = await r.get(key)
    return int(val) if val else 0


async def reset_counter(key: str):
    r = await get_redis()
    await r.set(key, 0)
