import sys
import os
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared-utils")))

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    REFRESH_TOKEN_EXPIRE_DAYS: int = 7
    EMAIL_SERVICE_URL: str = "http://email-service:8005"
    EMAIL_VERIFICATION_CODE_EXPIRE_MINUTES: int = 15
    MAX_VERIFICATION_ATTEMPTS: int = 3
    EMAIL_SERVICE_GENERATE_TIMEOUT: float = 10.0
    EMAIL_SERVICE_SEND_TIMEOUT: float = 30.0

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
