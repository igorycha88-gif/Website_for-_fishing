import secrets
import redis.asyncio as redis
from app.core.config import settings
from app.core.logging_config import get_logger
from typing import Optional

logger = get_logger(__name__)


class CSRFProtection:
    """
    CSRF Protection using Synchronizer Token Pattern.
    
    Stores CSRF tokens in Redis with TTL.
    """
    
    def __init__(self, redis_client: redis.Redis):
        self.redis = redis_client
        self.prefix = "csrf"
        self.ttl = settings.CSRF_TOKEN_TTL
    
    async def generate_token(self, user_id: str) -> str:
        """
        Generate CSRF token and store in Redis.
        
        Args:
            user_id: User UUID
        
        Returns:
            str: 43-char CSRF token
        """
        token = secrets.token_urlsafe(32)
        key = f"{self.prefix}:{user_id}"
        
        await self.redis.setex(key, self.ttl, token)
        
        logger.info(
            "CSRF token generated",
            user_id=user_id,
            ttl=self.ttl
        )
        
        return token
    
    async def validate_token(self, user_id: str, token: str) -> bool:
        """
        Validate CSRF token against Redis.
        
        Args:
            user_id: User UUID
            token: CSRF token from request
        
        Returns:
            bool: True if valid, False otherwise
        """
        if not token:
            logger.warning("CSRF token missing", user_id=user_id)
            return False
        
        key = f"{self.prefix}:{user_id}"
        
        try:
            stored = await self.redis.get(key)
        except redis.RedisError as e:
            logger.warning(
                "Redis unavailable, skipping CSRF validation",
                user_id=user_id,
                error=str(e)
            )
            return True
        
        if not stored:
            logger.warning("CSRF token not found in Redis", user_id=user_id)
            return False
        
        stored_str = stored.decode() if isinstance(stored, bytes) else stored
        
        if not secrets.compare_digest(stored_str, token):
            logger.warning(
                "CSRF token mismatch",
                user_id=user_id,
                expected_prefix=stored_str[:8],
                received_prefix=token[:8]
            )
            return False
        
        logger.debug("CSRF token validated", user_id=user_id)
        return True
    
    async def invalidate_token(self, user_id: str) -> bool:
        """
        Invalidate CSRF token (delete from Redis).
        
        Args:
            user_id: User UUID
        
        Returns:
            bool: True if deleted, False if not found
        """
        key = f"{self.prefix}:{user_id}"
        
        try:
            deleted = await self.redis.delete(key)
        except redis.RedisError as e:
            logger.warning(
                "Redis unavailable during CSRF token invalidation",
                user_id=user_id,
                error=str(e)
            )
            return False
        
        if deleted:
            logger.info("CSRF token invalidated", user_id=user_id)
        else:
            logger.debug("CSRF token not found for invalidation", user_id=user_id)
        
        return deleted > 0
    
    async def refresh_token(self, user_id: str) -> str:
        """
        Refresh CSRF token (invalidate old, generate new).
        
        Args:
            user_id: User UUID
        
        Returns:
            str: New CSRF token
        """
        await self.invalidate_token(user_id)
        return await self.generate_token(user_id)


_csrf_protection: Optional[CSRFProtection] = None


async def init_csrf_protection(redis_client: redis.Redis) -> CSRFProtection:
    """Initialize global CSRF protection instance."""
    global _csrf_protection
    _csrf_protection = CSRFProtection(redis_client)
    logger.info("CSRF protection initialized")
    return _csrf_protection


def get_csrf_protection() -> CSRFProtection:
    """Get global CSRF protection instance."""
    global _csrf_protection
    if _csrf_protection is None:
        raise RuntimeError("CSRF protection not initialized. Call init_csrf_protection() first.")
    return _csrf_protection
