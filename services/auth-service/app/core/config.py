import sys
import os
import logging
from urllib.parse import urlparse

sys.path.append(
    os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared-utils"))
)

from pydantic_settings import BaseSettings
from typing import Optional, List

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_SERVICE_URL: str = "http://email-service:8005"
    EMAIL_SERVICE_API_KEY: str = ""
    ENABLE_EMAIL_SENDING: bool = False
    EMAIL_CODE_EXPIRE_MINUTES: int = 15
    MAX_VERIFICATION_ATTEMPTS: int = 3
    EMAIL_SERVICE_GENERATE_TIMEOUT: float = 10.0
    EMAIL_SERVICE_SEND_TIMEOUT: float = 30.0
    FRONTEND_URL: str = "http://localhost:3000"
    LOG_LEVEL: str = "INFO"
    LOGSTASH_URL: str = "http://logstash:5000"
    SERVICE_NAME: str = "auth-service"
    YANDEX_MAPS_API_KEY: str = "dfb59053-0011-47fb-a6f1-a14efb9160d1"
    ENVIRONMENT: str = "production"
    DEV_EMAIL_DOMAIN: str = "test.localhost"
    CORS_ORIGINS: str = ""

    USE_VAULT: bool = False
    VAULT_ADDR: str = "http://vault:8200"
    VAULT_ROLE_ID: Optional[str] = None
    VAULT_SECRET_ID: Optional[str] = None

    RATE_LIMIT_ENABLED: bool = True
    RATE_LIMIT_LOGIN: str = "5/minute"
    RATE_LIMIT_REGISTER: str = "10/hour"
    RATE_LIMIT_RESET_PASSWORD: str = "3/hour"
    RATE_LIMIT_VERIFY_EMAIL: str = "5/minute"

    CSRF_ENABLED: bool = True
    CSRF_TOKEN_TTL: int = 86400

    class Config:
        env_file = os.path.join(os.path.dirname(__file__), "../../../../.env")
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

    def load_secrets_from_vault(self) -> None:
        if not self.USE_VAULT:
            logger.debug("Vault disabled, using environment secrets")
            return

        try:
            from vault_client import get_vault_client

            vault = get_vault_client()

            if not vault.is_available():
                logger.warning("Vault not available, using environment secrets")
                return

            if not self.SECRET_KEY or self.SECRET_KEY == "your-secret-key-change-in-production-min-32-chars":
                vault_secret = vault.get_jwt_secret()
                if vault_secret:
                    self.SECRET_KEY = vault_secret
                    logger.info("Loaded SECRET_KEY from Vault")

            logger.info("Secrets loaded from Vault")
        except Exception as e:
            logger.error(f"Failed to load secrets from Vault: {e}")
            if not self.SECRET_KEY:
                raise ValueError("SECRET_KEY not available from Vault or environment")


settings = Settings()
settings.load_secrets_from_vault()

if not settings.SECRET_KEY or len(settings.SECRET_KEY) < 32:
    if settings.USE_VAULT:
        pass
    else:
        raise ValueError("SECRET_KEY must be at least 32 characters")
