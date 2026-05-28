from pydantic_settings import BaseSettings


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

    LOG_LEVEL: str = "INFO"
    LOGSTASH_URL: str = "http://logstash:5000"
    SERVICE_NAME: str = "email-service"

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
