import pytest
from unittest.mock import AsyncMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.email import send_verification_email, generate_verification_code


@pytest.mark.asyncio
async def test_generate_verification_code_length():
    code = generate_verification_code()
    assert len(code) == 6
    assert code.isdigit()


@pytest.mark.asyncio
async def test_generate_verification_code_uniqueness():
    code1 = generate_verification_code()
    code2 = generate_verification_code()
    assert code1 != code2


@pytest.mark.asyncio
async def test_generate_verification_code_range():
    code = generate_verification_code()
    for digit in code:
        assert 0 <= int(digit) <= 9


@pytest.mark.asyncio
async def test_send_verification_email_success():
    to_email = "test@example.com"
    verification_code = "123456"
    username = "testuser"

    with patch("app.core.email.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None

        result = await send_verification_email(to_email, verification_code, username)

        assert result is True
        mock_send.assert_called_once()
        call_kwargs = mock_send.call_args[1]
        assert call_kwargs["hostname"] == "smtp.yandex.ru"
        assert call_kwargs["port"] == 465
        assert call_kwargs["use_tls"] is True


@pytest.mark.asyncio
async def test_send_verification_email_failure():
    to_email = "test@example.com"
    verification_code = "123456"
    username = "testuser"

    with patch("app.core.email.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = Exception("SMTP connection failed")

        result = await send_verification_email(to_email, verification_code, username)

        assert result is False
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_send_verification_email_html_content():
    to_email = "test@example.com"
    verification_code = "654321"
    username = "john_doe"

    with patch("app.core.email.aiosmtplib.send", new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None

        await send_verification_email(to_email, verification_code, username)

        call_args = mock_send.call_args
        message = call_args[0][0]

        assert verification_code in str(message)
        assert username in str(message)
        assert "FishMap" in str(message)
        assert "подтверждения регистрации" in str(message)
