from pydantic_settings import BaseSettings
import logging

logger = logging.getLogger(__name__)


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://postgres:postgres@localhost:5432/fishing_db"
    REDIS_URL: str = "redis://localhost:6379/0"
    OPENWEATHERMAP_API_KEY: str = ""
    OPENWEATHERMAP_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    OPEN_METEO_BASE_URL: str = "https://api.open-meteo.com/v1"
    LOG_LEVEL: str = "INFO"
    LOGSTASH_URL: str = "http://logstash:5000"
    SERVICE_NAME: str = "forecast-service"
    WEATHER_CACHE_TTL: int = 3600

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
