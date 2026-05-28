from fastapi import FastAPI, Request
from fastapi_limiter import FastAPILimiter
from fastapi_limiter.depends import RateLimiter
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def init_rate_limiter(app: FastAPI) -> None:
    if not settings.RATE_LIMIT_ENABLED:
        logger.info("Rate limiting is disabled")
        return

    try:
        redis_client = redis.from_url(
            settings.REDIS_URL,
            encoding="utf-8",
            decode_responses=True
        )
        await FastAPILimiter.init(redis_client)
        logger.info("Rate limiter initialized successfully")
    except Exception as e:
        logger.error(f"Failed to initialize rate limiter: {e}")
        raise


def get_client_ip(request: Request) -> str:
    forwarded = request.headers.get("X-Forwarded-For")
    if forwarded:
        return forwarded.split(",")[0].strip()
    return request.client.host if request.client else "unknown"


class RateLimitExceededError(Exception):
    def __init__(self, retry_after: int, limit: str, endpoint: str):
        self.retry_after = retry_after
        self.limit = limit
        self.endpoint = endpoint
        super().__init__(f"Rate limit exceeded for {endpoint}")
