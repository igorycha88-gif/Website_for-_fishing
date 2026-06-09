from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    SECRET_KEY: str
    ALGORITHM: str = "HS256"
    ACCESS_TOKEN_EXPIRE_MINUTES: int = 30
    YANDEX_MAPS_API_KEY: str = "dfb59053-0011-47fb-a6f1-a14efb9160d1"
    AUTH_SERVICE_URL: str = "http://auth-service:8001"
    DEFAULT_LAT: float = 55.7558
    DEFAULT_LNG: float = 37.6173
    DEFAULT_ZOOM: int = 10

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
