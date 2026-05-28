from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=".env",
        case_sensitive=True
    )

    SMTP_HOST: str = "smtp.yandex.ru"
    SMTP_PORT: int = 465
    SMTP_USER: str
    SMTP_PASSWORD: str
    SMTP_FROM_EMAIL: str
    SMTP_FROM_NAME: str = "FishMap"

    EMAIL_CODE_EXPIRE_MINUTES: int = 15
    EMAIL_CODE_LENGTH: int = 6

    EMAIL_TYPES: dict = {
        "verification": "Подтверждение регистрации",
        "password_reset": "Сброс пароля"
    }
