from pydantic_settings import BaseSettings
from typing import Optional
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    OPENWEATHERMAP_API_KEY: str
    OPENWEATHERMAP_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    LOG_LEVEL: str = "INFO"
    LOGSTASH_URL: str = "http://logstash:5000"
    SERVICE_NAME: str = "forecast-service"
    WEATHER_CACHE_TTL: int = 3600

    USE_VAULT: bool = False
    VAULT_ADDR: str = "http://vault:8200"
    VAULT_ROLE_ID: Optional[str] = None
    VAULT_SECRET_ID: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

    def load_secrets_from_vault(self) -> None:
        if not self.USE_VAULT:
            logger.debug("Vault disabled, using environment secrets")
            return

        try:
            import sys
            import os
            sys.path.append(
                os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared-utils"))
            )
            from vault_client import get_vault_client

            vault = get_vault_client()

            if not vault.is_available():
                logger.warning("Vault not available, using environment secrets")
                return

            if not self.OPENWEATHERMAP_API_KEY:
                vault_key = vault.get_weather_api_key()
                if vault_key:
                    self.OPENWEATHERMAP_API_KEY = vault_key
                    logger.info("Loaded OPENWEATHERMAP_API_KEY from Vault")

            logger.info("Secrets loaded from Vault")
        except Exception as e:
            logger.error(f"Failed to load secrets from Vault: {e}")


settings = Settings()
settings.load_secrets_from_vault()
