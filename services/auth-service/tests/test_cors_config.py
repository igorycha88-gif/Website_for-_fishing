import pytest
from unittest.mock import patch
from app.core.config import Settings


class TestCorsOriginsList:
    def test_development_mode_adds_localhost_origins(self):
        with patch.dict("os.environ", {
            "DATABASE_URL": "postgresql+asyncpg://test",
            "REDIS_URL": "redis://test",
            "SECRET_KEY": "test-secret-key-min-32-characters-long",
            "ENVIRONMENT": "development",
            "CORS_ORIGINS": ""
        }):
            settings = Settings()
            origins = settings.cors_origins_list
            
            assert "http://localhost:3000" in origins
            assert "http://127.0.0.1:3000" in origins
            assert "http://localhost:3001" in origins

    def test_production_mode_no_localhost_fallback(self):
        with patch.dict("os.environ", {
            "DATABASE_URL": "postgresql+asyncpg://test",
            "REDIS_URL": "redis://test",
            "SECRET_KEY": "test-secret-key-min-32-characters-long",
            "ENVIRONMENT": "production",
            "CORS_ORIGINS": "https://example.com"
        }):
            settings = Settings()
            origins = settings.cors_origins_list
            
            assert "http://localhost:3000" not in origins
            assert "https://example.com" in origins

    def test_parses_comma_separated_origins(self):
        with patch.dict("os.environ", {
            "DATABASE_URL": "postgresql+asyncpg://test",
            "REDIS_URL": "redis://test",
            "SECRET_KEY": "test-secret-key-min-32-characters-long",
            "ENVIRONMENT": "production",
            "CORS_ORIGINS": "https://example.com,https://api.example.com"
        }):
            settings = Settings()
            origins = settings.cors_origins_list
            
            assert "https://example.com" in origins
            assert "https://api.example.com" in origins
            assert len(origins) == 2

    def test_development_mode_combines_env_and_localhost(self):
        with patch.dict("os.environ", {
            "DATABASE_URL": "postgresql+asyncpg://test",
            "REDIS_URL": "redis://test",
            "SECRET_KEY": "test-secret-key-min-32-characters-long",
            "ENVIRONMENT": "development",
            "CORS_ORIGINS": "https://example.com"
        }):
            settings = Settings()
            origins = settings.cors_origins_list
            
            assert "http://localhost:3000" in origins
            assert "https://example.com" in origins
            assert len(origins) == 4

    def test_strips_whitespace_from_origins(self):
        with patch.dict("os.environ", {
            "DATABASE_URL": "postgresql+asyncpg://test",
            "REDIS_URL": "redis://test",
            "SECRET_KEY": "test-secret-key-min-32-characters-long",
            "ENVIRONMENT": "production",
            "CORS_ORIGINS": "  https://example.com  ,  https://api.example.com  "
        }):
            settings = Settings()
            origins = settings.cors_origins_list
            
            assert "https://example.com" in origins
            assert "https://api.example.com" in origins


class TestValidateOrigin:
    def test_valid_url(self):
        with patch.dict("os.environ", {
            "DATABASE_URL": "postgresql+asyncpg://test",
            "REDIS_URL": "redis://test",
            "SECRET_KEY": "test-secret-key-min-32-characters-long"
        }):
            settings = Settings()
            
            assert settings._validate_origin("https://example.com") is True
            assert settings._validate_origin("http://localhost:3000") is True
            assert settings._validate_origin("https://api.example.com:8080") is True

    def test_invalid_url(self):
        with patch.dict("os.environ", {
            "DATABASE_URL": "postgresql+asyncpg://test",
            "REDIS_URL": "redis://test",
            "SECRET_KEY": "test-secret-key-min-32-characters-long"
        }):
            settings = Settings()
            
            assert settings._validate_origin("invalid-url") is False
            assert settings._validate_origin("example.com") is False
            assert settings._validate_origin("//example.com") is False

    def test_wildcard_origin(self):
        with patch.dict("os.environ", {
            "DATABASE_URL": "postgresql+asyncpg://test",
            "REDIS_URL": "redis://test",
            "SECRET_KEY": "test-secret-key-min-32-characters-long"
        }):
            settings = Settings()
            
            assert settings._validate_origin("*") is True

    def test_empty_string(self):
        with patch.dict("os.environ", {
            "DATABASE_URL": "postgresql+asyncpg://test",
            "REDIS_URL": "redis://test",
            "SECRET_KEY": "test-secret-key-min-32-characters-long"
        }):
            settings = Settings()
            
            assert settings._validate_origin("") is False


class TestInvalidOriginLogging:
    def test_invalid_origin_is_excluded(self, caplog):
        with patch.dict("os.environ", {
            "DATABASE_URL": "postgresql+asyncpg://test",
            "REDIS_URL": "redis://test",
            "SECRET_KEY": "test-secret-key-min-32-characters-long",
            "ENVIRONMENT": "production",
            "CORS_ORIGINS": "invalid-url,https://valid.com"
        }):
            with caplog.at_level("WARNING"):
                settings = Settings()
                origins = settings.cors_origins_list
            
            assert "https://valid.com" in origins
            assert "invalid-url" not in origins
            assert any("Invalid CORS origin format" in record.message for record in caplog.records)

    def test_production_empty_origins_warning(self, caplog):
        with patch.dict("os.environ", {
            "DATABASE_URL": "postgresql+asyncpg://test",
            "REDIS_URL": "redis://test",
            "SECRET_KEY": "test-secret-key-min-32-characters-long",
            "ENVIRONMENT": "production",
            "CORS_ORIGINS": ""
        }):
            with caplog.at_level("WARNING"):
                settings = Settings()
                settings.cors_origins_list
            
            assert any("CORS_ORIGINS is empty in production mode" in record.message for record in caplog.records)

    def test_wildcard_warning(self, caplog):
        with patch.dict("os.environ", {
            "DATABASE_URL": "postgresql+asyncpg://test",
            "REDIS_URL": "redis://test",
            "SECRET_KEY": "test-secret-key-min-32-characters-long",
            "ENVIRONMENT": "production",
            "CORS_ORIGINS": "*"
        }):
            with caplog.at_level("WARNING"):
                settings = Settings()
                origins = settings.cors_origins_list
            
            assert "*" in origins
            assert any("Wildcard CORS origin detected" in record.message for record in caplog.records)
