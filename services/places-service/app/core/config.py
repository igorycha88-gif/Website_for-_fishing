import sys
import os
import logging
from urllib.parse import urlparse

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared-utils"))
)

from pydantic_settings import BaseSettings
from typing import List

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fishing_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    SECRET_KEY: str = "dev-secret-key-change-in-production-please-32ch"
    ALGORITHM: str = "HS256"
    LOG_LEVEL: str = "INFO"
    LOGSTASH_URL: str = "http://logstash:5000"
    SERVICE_NAME: str = "places-service"
    YANDEX_MAPS_API_KEY: str = "dfb59053-0011-47fb-a6f1-a14efb9160d1"
    ENVIRONMENT: str = "production"
    CORS_ORIGINS: str = ""

    class Config:
        env_file = ".env"
        case_sensitive = True

    @property
    def cors_origins_list(self) -> List[str]:
        origins: List[str] = []

        if self.ENVIRONMENT == "development":
            origins.extend([
                "http://localhost:3000",
                "http://127.0.0.1:3000",
                "http://localhost:3001",
            ])

        if self.CORS_ORIGINS:
            for origin in self.CORS_ORIGINS.split(","):
                origin = origin.strip()
                if not origin:
                    continue
                if origin == "*":
                    logger.warning("Wildcard CORS origin detected, this is not recommended")
                if not self._validate_origin(origin):
                    logger.warning(f"Invalid CORS origin format: {origin}")
                    continue
                origins.append(origin)

        if not origins and self.ENVIRONMENT == "production":
            logger.warning("CORS_ORIGINS is empty in production mode")

        return origins

    def _validate_origin(self, origin: str) -> bool:
        if origin == "*":
            return True
        try:
            result = urlparse(origin)
            return all([result.scheme, result.netloc])
        except Exception:
            return False


settings = Settings()
