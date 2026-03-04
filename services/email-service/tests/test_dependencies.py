import pytest
from fastapi import Request, HTTPException
from fastapi.testclient import TestClient
from unittest.mock import MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

os.environ.setdefault("SMTP_HOST", "smtp.yandex.ru")
os.environ.setdefault("SMTP_PORT", "465")
os.environ.setdefault("SMTP_USER", "test@example.com")
os.environ.setdefault("SMTP_PASSWORD", "test_password")
os.environ.setdefault("SMTP_FROM_EMAIL", "noreply@fishing.com")
os.environ.setdefault("SMTP_FROM_NAME", "FishMap")
os.environ.setdefault("EMAIL_SERVICE_API_KEY", "test-api-key-for-testing-min-32-chars")

from app.core.dependencies import verify_api_key
from app.core.config import settings


class TestVerifyApiKey:
    @pytest.mark.asyncio
    async def test_valid_api_key_returns_key(self):
        request = MagicMock(spec=Request)
        request.headers = {"X-API-Key": "test-api-key-for-testing-min-32-chars"}
        request.url = MagicMock()
        request.url.path = "/api/v1/email/generate-code"
        request.method = "POST"

        result = await verify_api_key(request)

        assert result == "test-api-key-for-testing-min-32-chars"

    @pytest.mark.asyncio
    async def test_missing_api_key_raises_401(self):
        request = MagicMock(spec=Request)
        request.headers = {}
        request.url = MagicMock()
        request.url.path = "/api/v1/email/generate-code"
        request.method = "POST"

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "API_KEY_REQUIRED"
        assert "X-API-Key header is required" in exc_info.value.detail["message"]

    @pytest.mark.asyncio
    async def test_invalid_api_key_raises_403(self):
        request = MagicMock(spec=Request)
        request.headers = {"X-API-Key": "wrong-api-key"}
        request.url = MagicMock()
        request.url.path = "/api/v1/email/generate-code"
        request.method = "POST"

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(request)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "INVALID_API_KEY"
        assert "Invalid API key" in exc_info.value.detail["message"]

    @pytest.mark.asyncio
    async def test_empty_api_key_raises_401(self):
        request = MagicMock(spec=Request)
        request.headers = {"X-API-Key": ""}
        request.url = MagicMock()
        request.url.path = "/api/v1/email/send"
        request.method = "POST"

        with pytest.raises(HTTPException) as exc_info:
            await verify_api_key(request)

        assert exc_info.value.status_code == 401
        assert exc_info.value.detail["code"] == "API_KEY_REQUIRED"
