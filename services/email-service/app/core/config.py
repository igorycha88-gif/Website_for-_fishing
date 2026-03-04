from pydantic_settings import BaseSettings
from typing import Optional
from pydantic import validator
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    SMTP_HOST: str = "smtp.yandex.ru"
    SMTP_PORT: int = 465
    SMTP_USER: str = ""
    SMTP_PASSWORD: str = ""
    SMTP_FROM_EMAIL: str = ""
    SMTP_FROM_NAME: str = "FishMap"

    ENABLE_EMAIL_SENDING: bool = False
    EMAIL_CODE_EXPIRE_MINUTES: int = 15
    EMAIL_CODE_LENGTH: int = 6

    EMAIL_SERVICE_API_KEY: str = ""

    LOG_LEVEL: str = "INFO"
    LOGSTASH_URL: str = "http://logstash:5000"
    SERVICE_NAME: str = "email-service"

    USE_VAULT: bool = False
    VAULT_ADDR: str = "http://vault:8200"
    VAULT_ROLE_ID: Optional[str] = None
    VAULT_SECRET_ID: Optional[str] = None

    class Config:
        env_file = ".env"
        case_sensitive = True

    @validator("EMAIL_SERVICE_API_KEY")
    def validate_api_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("EMAIL_SERVICE_API_KEY must be at least 32 characters")
        return v

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

            if not self.SMTP_PASSWORD:
                vault_password = vault.get_smtp_password()
                if vault_password:
                    self.SMTP_PASSWORD = vault_password
                    logger.info("Loaded SMTP_PASSWORD from Vault")

            logger.info("Secrets loaded from Vault")
        except Exception as e:
            logger.error(f"Failed to load secrets from Vault: {e}")


settings = Settings()
settings.load_secrets_from_vault()
