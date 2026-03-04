import pytest
from fastapi.testclient import TestClient
from unittest.mock import AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import app


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_send_email():
    with patch(
        "app.api.v1.router.send_verification_email", new_callable=AsyncMock
    ) as mock:
        mock.return_value = True
        yield mock


@pytest.fixture
def api_key():
    return "test-api-key-for-testing-min-32-chars"


@pytest.fixture
def api_headers(api_key):
    return {"X-API-Key": api_key}


def test_health_check(client):
    response = client.get("/")
    assert response.status_code == 200


class TestGenerateCodeEndpoint:
    def test_generate_code_with_valid_api_key(self, client, api_headers):
        response = client.post("/api/v1/email/generate-code", headers=api_headers)

        assert response.status_code == 200
        data = response.json()
        assert "code" in data
        assert len(data["code"]) == 6
        assert data["code"].isdigit()

    def test_generate_code_without_api_key(self, client):
        response = client.post("/api/v1/email/generate-code")

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "API_KEY_REQUIRED"

    def test_generate_code_with_invalid_api_key(self, client):
        headers = {"X-API-Key": "invalid-api-key"}
        response = client.post("/api/v1/email/generate-code", headers=headers)

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "INVALID_API_KEY"


class TestSendEmailEndpoint:
    def test_send_email_success(self, client, mock_send_email, api_headers):
        request_data = {
            "to_email": "test@example.com",
            "verification_code": "123456",
            "username": "testuser",
        }

        response = client.post("/api/v1/email/send", json=request_data, headers=api_headers)

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert data["message"] == "Email sent successfully"
        mock_send_email.assert_called_once_with(
            to_email="test@example.com", verification_code="123456", username="testuser"
        )

    def test_send_email_without_api_key(self, client):
        request_data = {
            "to_email": "test@example.com",
            "verification_code": "123456",
            "username": "testuser",
        }

        response = client.post("/api/v1/email/send", json=request_data)

        assert response.status_code == 401
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "API_KEY_REQUIRED"

    def test_send_email_with_invalid_api_key(self, client):
        request_data = {
            "to_email": "test@example.com",
            "verification_code": "123456",
            "username": "testuser",
        }
        headers = {"X-API-Key": "invalid-api-key"}

        response = client.post("/api/v1/email/send", json=request_data, headers=headers)

        assert response.status_code == 403
        data = response.json()
        assert "detail" in data
        assert data["detail"]["code"] == "INVALID_API_KEY"

    def test_send_email_failure(self, client, api_headers):
        request_data = {
            "to_email": "test@example.com",
            "verification_code": "123456",
            "username": "testuser",
        }

        with patch(
            "app.api.v1.router.send_verification_email", new_callable=AsyncMock
        ) as mock_send:
            mock_send.return_value = False

            response = client.post("/api/v1/email/send", json=request_data, headers=api_headers)

            assert response.status_code == 500
            data = response.json()
            assert "detail" in data
            assert "EMAIL_SEND_FAILED" in str(data["detail"])

    def test_send_email_invalid_email(self, client, api_headers):
        request_data = {
            "to_email": "invalid-email",
            "verification_code": "123456",
            "username": "testuser",
        }

        response = client.post("/api/v1/email/send", json=request_data, headers=api_headers)

        assert response.status_code == 422
