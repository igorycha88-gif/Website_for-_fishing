from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    SMTP_HOST: str = "smtp.yandex.ru"
    SMTP_PORT: int = 465
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str = "FishMap"

    EMAIL_CODE_EXPIRE_MINUTES: int = 15
    EMAIL_CODE_LENGTH: int = 6

    class Config:
        env_file = ".env"
        case_sensitive = True
