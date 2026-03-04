import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import datetime, timedelta
from uuid import uuid4
import sys
import os
import secrets

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from app.endpoints.auth import request_password_reset, confirm_password_reset
from app.schemas.auth import ResetPasswordRequest, ResetPasswordConfirm
from app.models.user import User
from app.models.password_reset_token import PasswordResetToken
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
         patch("app.endpoints.auth.PasswordResetTokenCRUD") as MockPasswordResetTokenCRUD, \
         patch("app.endpoints.auth.settings") as mock_settings:
        
        mock_user_crud = AsyncMock()
        mock_user_crud.get_by_email.return_value = sample_user
        MockUserCRUD.return_value = mock_user_crud
        
        mock_token_crud = AsyncMock()
        mock_token_crud.invalidate_user_tokens.return_value = 0
        mock_token_crud.create.return_value = MagicMock(spec=PasswordResetToken)
        MockPasswordResetTokenCRUD.return_value = mock_token_crud
        
        mock_settings.ENABLE_EMAIL_SENDING = False
        mock_settings.FRONTEND_URL = "http://localhost:3000"
        
        request_body = ResetPasswordRequest(email="test@example.com")
        
        result = await request_password_reset(request_body, mock_request, mock_db)
        
        assert result.message == "Если этот email зарегистрирован, инструкция по сбросу пароля будет отправлена"
        mock_user_crud.get_by_email.assert_called_once_with("test@example.com")
        mock_token_crud.invalidate_user_tokens.assert_called_once()
        mock_token_crud.create.assert_called_once()


@pytest.mark.asyncio
async def test_request_password_reset_user_not_found(mock_db, mock_request):
    with patch("app.endpoints.auth.UserCRUD") as MockUserCRUD, \
         patch("app.endpoints.auth.PasswordResetTokenCRUD") as MockPasswordResetTokenCRUD:
        
        mock_user_crud = AsyncMock()
        mock_user_crud.get_by_email.return_value = None
        MockUserCRUD.return_value = mock_user_crud
        
        mock_token_crud = AsyncMock()
        MockPasswordResetTokenCRUD.return_value = mock_token_crud
        
        request_body = ResetPasswordRequest(email="nonexistent@example.com")
        
        result = await request_password_reset(request_body, mock_request, mock_db)
        
        assert result.message == "Если этот email зарегистрирован, инструкция по сбросу пароля будет отправлена"
        mock_user_crud.get_by_email.assert_called_once_with("nonexistent@example.com")
        mock_token_crud.invalidate_user_tokens.assert_not_called()
        mock_token_crud.create.assert_not_called()


@pytest.mark.asyncio
async def test_request_password_reset_invalidate_old_tokens(mock_db, mock_request, sample_user):
    with patch("app.endpoints.auth.UserCRUD") as MockUserCRUD, \
         patch("app.endpoints.auth.PasswordResetTokenCRUD") as MockPasswordResetTokenCRUD, \
         patch("app.endpoints.auth.settings") as mock_settings:
        
        mock_user_crud = AsyncMock()
        mock_user_crud.get_by_email.return_value = sample_user
        MockUserCRUD.return_value = mock_user_crud
        
        mock_token_crud = AsyncMock()
        mock_token_crud.invalidate_user_tokens.return_value = 2
        mock_token_crud.create.return_value = MagicMock(spec=PasswordResetToken)
        MockPasswordResetTokenCRUD.return_value = mock_token_crud
        
        mock_settings.ENABLE_EMAIL_SENDING = False
        mock_settings.FRONTEND_URL = "http://localhost:3000"
        
        request_body = ResetPasswordRequest(email="test@example.com")
        
        result = await request_password_reset(request_body, mock_request, mock_db)
        
        assert result.message == "Если этот email зарегистрирован, инструкция по сбросу пароля будет отправлена"
        mock_token_crud.invalidate_user_tokens.assert_called_once_with(str(sample_user.id))
        assert mock_token_crud.invalidate_user_tokens.return_value == 2


@pytest.mark.asyncio
async def test_confirm_password_reset_valid_token(mock_db, mock_request, sample_user):
    token = secrets.token_urlsafe(48)
    token_hash = get_password_hash(token)
    
    mock_token = MagicMock(spec=PasswordResetToken)
    mock_token.id = uuid4()
    mock_token.user_id = sample_user.id
    mock_token.token_hash = token_hash
    mock_token.used = False
    mock_token.expires_at = datetime.utcnow() + timedelta(hours=1)
    
    with patch("app.endpoints.auth.PasswordResetTokenCRUD") as MockPasswordResetTokenCRUD, \
         patch("app.endpoints.auth.UserCRUD") as MockUserCRUD, \
         patch("app.endpoints.auth.verify_password") as mock_verify, \
         patch("app.endpoints.auth.select") as mock_select, \
         patch("app.endpoints.auth.settings") as mock_settings:
        
        mock_token_crud = AsyncMock()
        mock_token_crud.mark_as_used.return_value = True
        MockPasswordResetTokenCRUD.return_value = mock_token_crud
        
        mock_user_crud = AsyncMock()
        mock_user_crud.get_by_id.return_value = sample_user
        mock_user_crud.update_password = AsyncMock()
        mock_user_crud.increment_token_version = AsyncMock()
        MockUserCRUD.return_value = mock_user_crud
        
        mock_verify.return_value = True
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_token]
        mock_db.execute.return_value = mock_result
        
        mock_select.return_value = MagicMock()
        
        mock_settings.ENABLE_EMAIL_SENDING = False
        
        request_body = ResetPasswordConfirm(token=token, new_password="NewPassword123")
        
        result = await confirm_password_reset(request_body, mock_request, mock_db)
        
        assert result.message == "Пароль успешно изменен"
        mock_token_crud.mark_as_used.assert_called_once()
        mock_user_crud.update_password.assert_called_once()
        mock_user_crud.increment_token_version.assert_called_once()


@pytest.mark.asyncio
async def test_confirm_password_reset_invalid_token_length(mock_db, mock_request):
    with patch("app.endpoints.auth.PasswordResetTokenCRUD") as MockPasswordResetTokenCRUD, \
         patch("app.endpoints.auth.UserCRUD") as MockUserCRUD:
        
        request_body = ResetPasswordConfirm(token="short", new_password="NewPassword123")
        
        with pytest.raises(Exception) as exc_info:
            await confirm_password_reset(request_body, mock_request, mock_db)
        
        assert "Invalid or expired token" in str(exc_info.value)


@pytest.mark.asyncio
async def test_confirm_password_reset_token_not_found(mock_db, mock_request):
    token = secrets.token_urlsafe(48)
    
    with patch("app.endpoints.auth.PasswordResetTokenCRUD") as MockPasswordResetTokenCRUD, \
         patch("app.endpoints.auth.verify_password") as mock_verify, \
         patch("app.endpoints.auth.select") as mock_select:
        
        mock_token_crud = AsyncMock()
        MockPasswordResetTokenCRUD.return_value = mock_token_crud
        
        mock_verify.return_value = False
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        mock_select.return_value = MagicMock()
        
        request_body = ResetPasswordConfirm(token=token, new_password="NewPassword123")
        
        with pytest.raises(Exception) as exc_info:
            await confirm_password_reset(request_body, mock_request, mock_db)
        
        assert "Invalid or expired token" in str(exc_info.value)


@pytest.mark.asyncio
async def test_confirm_password_reset_token_expired(mock_db, mock_request, sample_user):
    token = secrets.token_urlsafe(48)
    token_hash = get_password_hash(token)
    
    mock_token = MagicMock(spec=PasswordResetToken)
    mock_token.id = uuid4()
    mock_token.user_id = sample_user.id
    mock_token.token_hash = token_hash
    mock_token.used = False
    mock_token.expires_at = datetime.utcnow() - timedelta(hours=1)
    
    with patch("app.endpoints.auth.PasswordResetTokenCRUD") as MockPasswordResetTokenCRUD, \
         patch("app.endpoints.auth.verify_password") as mock_verify, \
         patch("app.endpoints.auth.select") as mock_select:
        
        mock_token_crud = AsyncMock()
        MockPasswordResetTokenCRUD.return_value = mock_token_crud
        
        mock_verify.return_value = True
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = [mock_token]
        mock_db.execute.return_value = mock_result
        
        mock_select.return_value = MagicMock()
        
        request_body = ResetPasswordConfirm(token=token, new_password="NewPassword123")
        
        with pytest.raises(Exception) as exc_info:
            await confirm_password_reset(request_body, mock_request, mock_db)
        
        assert "Invalid or expired token" in str(exc_info.value)


@pytest.mark.asyncio
async def test_confirm_password_reset_token_used(mock_db, mock_request):
    token = secrets.token_urlsafe(48)
    token_hash = get_password_hash(token)
    
    mock_token = MagicMock(spec=PasswordResetToken)
    mock_token.id = uuid4()
    mock_token.token_hash = token_hash
    mock_token.used = True
    
    with patch("app.endpoints.auth.PasswordResetTokenCRUD") as MockPasswordResetTokenCRUD, \
         patch("app.endpoints.auth.select") as mock_select:
        
        mock_token_crud = AsyncMock()
        MockPasswordResetTokenCRUD.return_value = mock_token_crud
        
        mock_result = MagicMock()
        mock_result.scalars.return_value.all.return_value = []
        mock_db.execute.return_value = mock_result
        
        mock_select.return_value = MagicMock()
        
        request_body = ResetPasswordConfirm(token=token, new_password="NewPassword123")
        
        with pytest.raises(Exception) as exc_info:
            await confirm_password_reset(request_body, mock_request, mock_db)
        
        assert "Invalid or expired token" in str(exc_info.value)
