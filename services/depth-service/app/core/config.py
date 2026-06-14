from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    LOG_LEVEL: str = "INFO"
    LOGSTASH_URL: str = "http://logstash:5000"
    SERVICE_NAME: str = "depth-service"
    GEBCO_WMS_URL: str = "https://wms.gebco.net/mapserv"
    GEBCO_WMS_LAYER: str = "GEBCO_LATEST"
    GEBCO_QUERY_LAYER: str = "GEBCO_LATEST_2"
    GEBCO_GEOTIFF_PATH: str = ""
    TILE_CACHE_DIR: str = "/tmp/depth_tiles"
    REDIS_URL: str = "redis://redis:6379/0"
    RATE_LIMIT_PER_MIN: int = 60

    OVERPASS_API_URL: str = "https://overpass-api.de/api/interpreter"
    OVERPASS_TIMEOUT: int = 10
    OVERPASS_SEARCH_RADIUS_M: int = 50

    DEPTH_CACHE_TTL: int = 86400

    DATABASE_URL: str = (
        "postgresql+asyncpg://postgres:postgres_password@postgres:5432/fishing_db"
    )

    class Config:
        env_file = ".env"
        case_sensitive = True


settings = Settings()
