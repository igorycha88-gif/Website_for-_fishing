import pytest
from unittest.mock import AsyncMock, patch

from app.core.email import (
    _create_verification_email_html,
    _create_verification_email_text,
    _create_password_reset_email_html,
    _create_password_reset_email_text,
    _send_email,
    send_verification_email,
    send_password_reset_email,
    generate_verification_code
)


@pytest.mark.asyncio
async def test_create_verification_email_html():
    code = "123456"
    username = "testuser"

    html = _create_verification_email_html(code, username)

    assert code in html
    assert username in html
    assert "FishMap" in html
    assert "регистрации" in html
    assert "15 минут" in html


@pytest.mark.asyncio
async def test_create_verification_email_text():
    code = "123456"
    username = "testuser"

    text = _create_verification_email_text(code, username)

    assert code in text
    assert username in text
    assert "FishMap" in text
    assert "регистрации" in text
    assert "15 минут" in text


@pytest.mark.asyncio
async def test_create_password_reset_email_html():
    code = "654321"
    username = "testuser"

    html = _create_password_reset_email_html(code, username)

    assert code in html
    assert username in html
    assert "FishMap" in html
    assert "сброса пароля" in html
    assert "15 минут" in html
    assert "Внимание" in html


@pytest.mark.asyncio
async def test_create_password_reset_email_text():
    code = "654321"
    username = "testuser"

    text = _create_password_reset_email_text(code, username)

    assert code in text
    assert username in text
    assert "FishMap" in text
    assert "сброса пароля" in text
    assert "15 минут" in text
    assert "ВНИМАНИЕ" in text


@pytest.mark.asyncio
async def test_send_email_success():
    to_email = "test@example.com"
    subject = "Test Subject"
    html_content = "<html><body>Test</body></html>"
    text_content = "Test"

    with patch('app.core.email.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = None

        result = await _send_email(to_email, subject, html_content, text_content)

        assert result is True
        mock_send.assert_called_once()


@pytest.mark.asyncio
async def test_send_email_failure():
    to_email = "test@example.com"
    subject = "Test Subject"
    html_content = "<html><body>Test</body></html>"
    text_content = "Test"

    with patch('app.core.email.aiosmtplib.send', new_callable=AsyncMock) as mock_send:
        mock_send.side_effect = Exception("SMTP error")

        result = await _send_email(to_email, subject, html_content, text_content)

        assert result is False


@pytest.mark.asyncio
async def test_send_verification_email():
    to_email = "test@example.com"
    verification_code = "123456"
    username = "testuser"

    with patch('app.core.email._send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        result = await send_verification_email(to_email, verification_code, username)

        assert result is True
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        assert to_email in call_args
        assert "подтверждения регистрации" in call_args[1]


@pytest.mark.asyncio
async def test_send_password_reset_email():
    to_email = "test@example.com"
    verification_code = "654321"
    username = "testuser"

    with patch('app.core.email._send_email', new_callable=AsyncMock) as mock_send:
        mock_send.return_value = True

        result = await send_password_reset_email(to_email, verification_code, username)

        assert result is True
        mock_send.assert_called_once()
        call_args = mock_send.call_args[0]
        assert to_email in call_args
        assert "сброса пароля" in call_args[1]


def test_generate_verification_code_length():
    code = generate_verification_code()

    assert len(code) == 6
    assert code.isdigit()


def test_generate_verification_code_uniqueness():
    code1 = generate_verification_code()
    code2 = generate_verification_code()

    assert code1 != code2


def test_generate_verification_code_range():
    code = generate_verification_code()

    for digit in code:
        assert 0 <= int(digit) <= 9
