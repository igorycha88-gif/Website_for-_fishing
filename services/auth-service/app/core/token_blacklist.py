import redis.asyncio as redis
from app.core.config import settings
from app.core.logging_config import get_logger
from typing import Optional

logger = get_logger(__name__)


class TokenBlacklist:
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.access_prefix = "blacklist:access"
        self.refresh_prefix = "blacklist:refresh"
    
    async def add_access_token(self, jti: str, expires_in_seconds: int) -> bool:
        key = f"{self.access_prefix}:{jti}"
        try:
            await self.redis.setex(key, expires_in_seconds, "1")
            logger.info("Access token blacklisted", jti=jti, ttl=expires_in_seconds)
            return True
        except Exception as e:
            logger.error("Failed to blacklist access token", jti=jti, error=str(e), exc_info=True)
            return False
    
    async def add_refresh_token(self, jti: str, expires_in_seconds: int) -> bool:
        key = f"{self.refresh_prefix}:{jti}"
        try:
            await self.redis.setex(key, expires_in_seconds, "1")
            logger.info("Refresh token blacklisted", jti=jti, ttl=expires_in_seconds)
            return True
        except Exception as e:
            logger.error("Failed to blacklist refresh token", jti=jti, error=str(e), exc_info=True)
            return False
    
    async def is_access_token_revoked(self, jti: str) -> bool:
        key = f"{self.access_prefix}:{jti}"
        try:
            exists = await self.redis.exists(key)
            return exists > 0
        except Exception as e:
            logger.warning("Redis unavailable during access token check", jti=jti, error=str(e))
            return False
    
    async def is_refresh_token_revoked(self, jti: str) -> bool:
        key = f"{self.refresh_prefix}:{jti}"
        try:
            exists = await self.redis.exists(key)
            return exists > 0
        except Exception as e:
            logger.warning("Redis unavailable during refresh token check", jti=jti, error=str(e))
            return False


_blacklist_instance: Optional[TokenBlacklist] = None


async def get_token_blacklist() -> TokenBlacklist:
    global _blacklist_instance
    if _blacklist_instance is None:
        from app.core.database import get_redis
        redis_client = await get_redis()
        _blacklist_instance = TokenBlacklist(redis_client)
    return _blacklist_instance
