import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from app.endpoints.auth import request_password_reset, confirm_password_reset
from app.schemas.auth import ResetPasswordRequest, ResetPasswordConfirm
from app.models.user import User
from app.models.email_verification_code import EmailVerificationCode
from app.core.security import get_password_hash


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def mock_request():
    request = MagicMock()
    request.client = MagicMock()
    request.client.host = "192.168.1.1"
    request.headers = {"user-agent": "Mozilla/5.0"}
    return request


@pytest.fixture
def sample_user():
    user = MagicMock(spec=User)
    user.id = uuid4()
    user.email = "test@example.com"
    user.username = "testuser"
    user.password_hash = get_password_hash("OldPassword123")
    user.token_version = 1
    return user


@pytest.mark.asyncio
async def test_request_password_reset_user_exists(mock_db, mock_request, sample_user):
    with patch("app.endpoints.auth.UserCRUD") as MockUserCRUD, \
         patch("app.endpoints.auth.EmailVerificationCodeCRUD") as MockEmailCodeCRUD, \
         patch("app.endpoints.auth.settings") as mock_settings:

        mock_user_crud = AsyncMock()
        mock_user_crud.get_by_email.return_value = sample_user
        MockUserCRUD.return_value = mock_user_crud

        mock_email_code_crud = AsyncMock()
        mock_email_code_crud.delete_by_email.return_value = True
        mock_email_code_crud.create.return_value = MagicMock()
        MockEmailCodeCRUD.return_value = mock_email_code_crud

        mock_settings.ENABLE_EMAIL_SENDING = False
        mock_settings.ENVIRONMENT = "development"
        mock_settings.EMAIL_CODE_EXPIRE_MINUTES = 15

        request_body = ResetPasswordRequest(email="test@example.com")

        result = await request_password_reset(request_body, mock_request, mock_db)

        assert result.message == "Если этот email зарегистрирован, код подтверждения будет отправлен"
        mock_user_crud.get_by_email.assert_called_once_with("test@example.com")
        mock_email_code_crud.delete_by_email.assert_called_once_with("test@example.com")
        mock_email_code_crud.create.assert_called_once()


@pytest.mark.asyncio
async def test_request_password_reset_user_not_found(mock_db, mock_request):
    with patch("app.endpoints.auth.UserCRUD") as MockUserCRUD:

        mock_user_crud = AsyncMock()
        mock_user_crud.get_by_email.return_value = None
        MockUserCRUD.return_value = mock_user_crud

        request_body = ResetPasswordRequest(email="nonexistent@example.com")

        result = await request_password_reset(request_body, mock_request, mock_db)

        assert result.message == "Если этот email зарегистрирован, код подтверждения будет отправлен"
        mock_user_crud.get_by_email.assert_called_once_with("nonexistent@example.com")


@pytest.mark.asyncio
async def test_confirm_password_reset_valid_code(mock_db, mock_request, sample_user):
    mock_verification = MagicMock(spec=EmailVerificationCode)
    mock_verification.email = "test@example.com"
    mock_verification.code = "ABC123"
    mock_verification.attempts = 0
    mock_verification.expires_at = datetime.utcnow() + timedelta(minutes=15)

    with patch("app.endpoints.auth.EmailVerificationCodeCRUD") as MockEmailCodeCRUD, \
         patch("app.endpoints.auth.UserCRUD") as MockUserCRUD, \
         patch("app.endpoints.auth.settings") as mock_settings:

        mock_email_code_crud = AsyncMock()
        mock_email_code_crud.get_valid_code.return_value = mock_verification
        mock_email_code_crud.delete_by_email.return_value = True
        MockEmailCodeCRUD.return_value = mock_email_code_crud

        mock_user_crud = AsyncMock()
        mock_user_crud.get_by_email.return_value = sample_user
        mock_user_crud.update_password = AsyncMock()
        mock_user_crud.increment_token_version = AsyncMock()
        MockUserCRUD.return_value = mock_user_crud

        mock_settings.ENABLE_EMAIL_SENDING = False

        request_body = ResetPasswordConfirm(
            email="test@example.com",
            code="ABC123",
            new_password="NewPassword123",
        )

        result = await confirm_password_reset(request_body, mock_request, mock_db)

        assert result.message == "Пароль успешно изменен"
        mock_user_crud.update_password.assert_called_once()
        mock_user_crud.increment_token_version.assert_called_once()
        mock_email_code_crud.delete_by_email.assert_called_once_with("test@example.com")


@pytest.mark.asyncio
async def test_confirm_password_reset_invalid_code(mock_db, mock_request):
    with patch("app.endpoints.auth.EmailVerificationCodeCRUD") as MockEmailCodeCRUD:

        mock_email_code_crud = AsyncMock()
        mock_email_code_crud.get_valid_code.return_value = None
        mock_email_code_crud.get_by_email.return_value = MagicMock(attempts=0)
        mock_email_code_crud.increment_attempts.return_value = None
        MockEmailCodeCRUD.return_value = mock_email_code_crud

        request_body = ResetPasswordConfirm(
            email="test@example.com",
            code="WRONG",
            new_password="NewPassword123",
        )

        with pytest.raises(Exception) as exc_info:
            await confirm_password_reset(request_body, mock_request, mock_db)

        assert exc_info.value.status_code == 400


@pytest.mark.asyncio
async def test_confirm_password_reset_user_not_found(mock_db, mock_request):
    mock_verification = MagicMock(spec=EmailVerificationCode)
    mock_verification.expires_at = datetime.utcnow() + timedelta(minutes=15)

    with patch("app.endpoints.auth.EmailVerificationCodeCRUD") as MockEmailCodeCRUD, \
         patch("app.endpoints.auth.UserCRUD") as MockUserCRUD:

        mock_email_code_crud = AsyncMock()
        mock_email_code_crud.get_valid_code.return_value = mock_verification
        mock_email_code_crud.delete_by_email.return_value = True
        MockEmailCodeCRUD.return_value = mock_email_code_crud

        mock_user_crud = AsyncMock()
        mock_user_crud.get_by_email.return_value = None
        MockUserCRUD.return_value = mock_user_crud

        request_body = ResetPasswordConfirm(
            email="test@example.com",
            code="ABC123",
            new_password="NewPassword123",
        )

        with pytest.raises(Exception) as exc_info:
            await confirm_password_reset(request_body, mock_request, mock_db)

        assert exc_info.value.status_code == 404


@pytest.mark.asyncio
async def test_confirm_password_reset_max_attempts(mock_db, mock_request):
    with patch("app.endpoints.auth.EmailVerificationCodeCRUD") as MockEmailCodeCRUD:

        mock_email_code_crud = AsyncMock()
        mock_email_code_crud.get_valid_code.return_value = None
        mock_email_code_crud.get_by_email.return_value = MagicMock(attempts=2)
        mock_email_code_crud.increment_attempts.return_value = None
        mock_email_code_crud.delete_by_email.return_value = True
        MockEmailCodeCRUD.return_value = mock_email_code_crud

        request_body = ResetPasswordConfirm(
            email="test@example.com",
            code="WRONG",
            new_password="NewPassword123",
        )

        with pytest.raises(Exception) as exc_info:
            await confirm_password_reset(request_body, mock_request, mock_db)

        assert exc_info.value.status_code == 400
        mock_email_code_crud.delete_by_email.assert_called_once()
