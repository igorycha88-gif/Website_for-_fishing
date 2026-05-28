import pytest
from unittest.mock import AsyncMock, patch
from httpx import AsyncClient

from app.main import app


@pytest.mark.asyncio
async def test_send_verification_email_success():
    email_data = {
        "to_email": "test@example.com",
        "verification_code": "123456",
        "username": "testuser",
        "email_type": "verification"
    }

    with patch('app.core.email._send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/email/send", json=email_data)

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "verification" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_send_password_reset_email_success():
    email_data = {
        "to_email": "test@example.com",
        "verification_code": "654321",
        "username": "testuser",
        "email_type": "password_reset"
    }

    with patch('app.core.email._send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/email/send", json=email_data)

        assert response.status_code == 200
        assert response.json()["success"] is True
        assert "password reset" in response.json()["message"].lower()


@pytest.mark.asyncio
async def test_send_email_invalid_type():
    email_data = {
        "to_email": "test@example.com",
        "verification_code": "123456",
        "username": "testuser",
        "email_type": "invalid_type"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/email/send", json=email_data)

    assert response.status_code == 400
    assert "INVALID_EMAIL_TYPE" in response.json()["detail"]["code"]


@pytest.mark.asyncio
async def test_send_email_smtp_failure():
    email_data = {
        "to_email": "test@example.com",
        "verification_code": "123456",
        "username": "testuser",
        "email_type": "verification"
    }

    with patch('app.core.email._send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = False

        async with AsyncClient(app=app, base_url="http://test") as client:
            response = await client.post("/api/v1/email/send", json=email_data)

        assert response.status_code == 500
        assert "EMAIL_SEND_FAILED" in response.json()["detail"]["code"]


@pytest.mark.asyncio
async def test_generate_code():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/email/generate-code")

    assert response.status_code == 200
    assert "code" in response.json()
    code = response.json()["code"]
    assert len(code) == 6
    assert code.isdigit()


@pytest.mark.asyncio
async def test_generate_code_uniqueness():
    async with AsyncClient(app=app, base_url="http://test") as client:
        response1 = await client.post("/api/v1/email/generate-code")
        response2 = await client.post("/api/v1/email/generate-code")

    assert response1.status_code == 200
    assert response2.status_code == 200
    code1 = response1.json()["code"]
    code2 = response2.json()["code"]
    assert code1 != code2


@pytest.mark.asyncio
async def test_send_email_validation():
    invalid_email_data = {
        "to_email": "invalid-email",
        "verification_code": "123456",
        "username": "testuser",
        "email_type": "verification"
    }

    async with AsyncClient(app=app, base_url="http://test") as client:
        response = await client.post("/api/v1/email/send", json=invalid_email_data)

    assert response.status_code == 422
