from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    DATABASE_URL: str
    REDIS_URL: str
    OPENWEATHERMAP_API_KEY: str
    OPENWEATHERMAP_BASE_URL: str = "https://api.openweathermap.org/data/2.5"
    LOG_LEVEL: str = "INFO"
    LOGSTASH_URL: str = "http://logstash:5000"
    SERVICE_NAME: str = "forecast-service"
    WEATHER_CACHE_TTL: int = 3600

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
