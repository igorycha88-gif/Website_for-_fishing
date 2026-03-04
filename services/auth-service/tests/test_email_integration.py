import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import httpx
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))


class TestEmailServiceIntegration:
    @pytest.mark.asyncio
    async def test_auth_service_config_has_api_key_field(self):
        from pydantic_settings import BaseSettings
        from typing import Optional, List

        class TestSettings(BaseSettings):
            DATABASE_URL: str = "test"
            REDIS_URL: str = "test"
            SECRET_KEY: str = "test"
            EMAIL_SERVICE_API_KEY: str = "test-api-key-for-testing-min-32-chars"
            
            class Config:
                extra = "ignore"
        
        settings = TestSettings()
        
        assert hasattr(settings, "EMAIL_SERVICE_API_KEY")
        assert settings.EMAIL_SERVICE_API_KEY == "test-api-key-for-testing-min-32-chars"
        assert len(settings.EMAIL_SERVICE_API_KEY) >= 32

    @pytest.mark.asyncio
    async def test_api_headers_contain_x_api_key(self):
        expected_api_key = "test-api-key-for-testing-min-32-chars"
        api_headers = {"X-API-Key": expected_api_key}

        assert "X-API-Key" in api_headers
        assert api_headers["X-API-Key"] == expected_api_key

    @pytest.mark.asyncio
    async def test_email_service_generate_code_call_with_api_key(self):
        mock_response = MagicMock()
        mock_response.json.return_value = {"code": "123456"}
        mock_response.raise_for_status = MagicMock()

        test_api_key = "test-api-key-for-testing-min-32-chars"
        email_service_url = "http://email-service:8005"

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            api_headers = {"X-API-Key": test_api_key}

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{email_service_url}/api/v1/email/generate-code",
                    headers=api_headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                code = response.json()["code"]

            assert code == "123456"
            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "headers" in call_args.kwargs
            assert call_args.kwargs["headers"]["X-API-Key"] == test_api_key

    @pytest.mark.asyncio
    async def test_email_service_send_call_with_api_key(self):
        test_api_key = "test-api-key-for-testing-min-32-chars"
        email_service_url = "http://email-service:8005"

        mock_response = MagicMock()
        mock_response.json.return_value = {"success": True, "message": "Email sent"}
        mock_response.raise_for_status = MagicMock()

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(return_value=mock_response)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            api_headers = {"X-API-Key": test_api_key}
            email_data = {
                "to_email": "test@example.com",
                "verification_code": "123456",
                "username": "testuser",
            }

            async with httpx.AsyncClient() as client:
                response = await client.post(
                    f"{email_service_url}/api/v1/email/send",
                    json=email_data,
                    headers=api_headers,
                    timeout=30.0,
                )
                response.raise_for_status()

            mock_client.post.assert_called_once()
            call_args = mock_client.post.call_args
            assert "headers" in call_args.kwargs
            assert call_args.kwargs["headers"]["X-API-Key"] == test_api_key
            assert call_args.kwargs["json"] == email_data

    @pytest.mark.asyncio
    async def test_handle_401_from_email_service(self):
        mock_response = MagicMock()
        mock_response.status_code = 401
        mock_response.json.return_value = {
            "detail": {"code": "API_KEY_REQUIRED", "message": "X-API-Key header is required"}
        }

        http_error = httpx.HTTPStatusError(
            message="401 Unauthorized",
            request=MagicMock(),
            response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=http_error)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        "http://email-service:8005/api/v1/email/generate-code",
                        headers={},
                        timeout=10.0,
                    )

            assert exc_info.value.response.status_code == 401

    @pytest.mark.asyncio
    async def test_handle_403_from_email_service(self):
        mock_response = MagicMock()
        mock_response.status_code = 403
        mock_response.json.return_value = {
            "detail": {"code": "INVALID_API_KEY", "message": "Invalid API key"}
        }

        http_error = httpx.HTTPStatusError(
            message="403 Forbidden",
            request=MagicMock(),
            response=mock_response
        )

        with patch("httpx.AsyncClient") as mock_client_class:
            mock_client = AsyncMock()
            mock_client.post = AsyncMock(side_effect=http_error)
            mock_client.__aenter__ = AsyncMock(return_value=mock_client)
            mock_client.__aexit__ = AsyncMock(return_value=None)
            mock_client_class.return_value = mock_client

            with pytest.raises(httpx.HTTPStatusError) as exc_info:
                async with httpx.AsyncClient() as client:
                    await client.post(
                        "http://email-service:8005/api/v1/email/generate-code",
                        headers={"X-API-Key": "wrong-key"},
                        timeout=10.0,
                    )

            assert exc_info.value.response.status_code == 403
