from pydantic_settings import BaseSettings
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

    class Config:
        env_file = ".env"
        case_sensitive = True

    @validator("EMAIL_SERVICE_API_KEY")
    def validate_api_key(cls, v: str) -> str:
        if len(v) < 32:
            raise ValueError("EMAIL_SERVICE_API_KEY must be at least 32 characters")
        return v


settings = Settings()
