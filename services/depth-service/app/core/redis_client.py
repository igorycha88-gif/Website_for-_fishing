import json

import redis.asyncio as aioredis

from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)

_redis: aioredis.Redis | None = None


async def get_redis() -> aioredis.Redis | None:
    global _redis
    if _redis is not None:
        return _redis
    try:
        pool = aioredis.ConnectionPool.from_url(
            settings.REDIS_URL,
            max_connections=10,
            decode_responses=True,
        )
        _redis = aioredis.Redis(connection_pool=pool)
        await _redis.ping()
        logger.info(
            "redis_connected",
            service="depth-service",
            action="redis_init",
        )
    except Exception as e:
        logger.warning(
            "redis_unavailable",
            service="depth-service",
            action="redis_init",
            error=str(e),
        )
        _redis = None
    return _redis


async def cache_get(key: str) -> dict | None:
    r = await get_redis()
    if r is None:
        return None
    try:
        raw = await r.get(key)
        if raw:
            return json.loads(raw)
    except Exception as e:
        logger.warning(
            "redis_cache_get_error",
            service="depth-service",
            action="redis_cache_get",
            error=str(e),
        )
    return None


async def cache_set(key: str, value: dict, ttl: int | None = None) -> None:
    r = await get_redis()
    if r is None:
        return
    try:
        effective_ttl = ttl or settings.DEPTH_CACHE_TTL
        await r.set(key, json.dumps(value), ex=effective_ttl)
    except Exception as e:
        logger.warning(
            "redis_cache_set_error",
            service="depth-service",
            action="redis_cache_set",
            error=str(e),
        )


async def close_redis() -> None:
    global _redis
    if _redis is not None:
        await _redis.aclose()
        _redis = None
