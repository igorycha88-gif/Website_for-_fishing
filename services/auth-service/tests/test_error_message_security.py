import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi import HTTPException, status
from fastapi import Request


class TestRegistrationGenericErrors:
    """Тесты для проверки generic error messages при регистрации"""

    @pytest.mark.asyncio
    async def test_registration_duplicate_email_returns_generic_error(self):
        """При регистрации с существующим email возвращается REGISTRATION_FAILED"""
        from app.endpoints.auth import register
        from app.schemas.auth import RegisterRequest
        
        mock_db = AsyncMock()
        mock_user_crud = MagicMock()
        mock_user_crud.get_by_email = AsyncMock(return_value=MagicMock(id="existing-id"))
        mock_user_crud.get_by_username = AsyncMock(return_value=None)
        
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        
        with patch('app.endpoints.auth.UserCRUD', return_value=mock_user_crud):
            request = RegisterRequest(
                email="existing@example.com",
                username="newuser",
                password="SecurePass123!"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await register(request, req=mock_request, db=mock_db)
            
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert exc_info.value.detail["code"] == "REGISTRATION_FAILED"
            assert "Unable to complete registration" in exc_info.value.detail["message"]
            assert "details" not in exc_info.value.detail
            assert "email" not in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_registration_duplicate_username_returns_generic_error(self):
        """При регистрации с существующим username возвращается REGISTRATION_FAILED"""
        from app.endpoints.auth import register
        from app.schemas.auth import RegisterRequest
        
        mock_db = AsyncMock()
        mock_user_crud = MagicMock()
        mock_user_crud.get_by_email = AsyncMock(return_value=None)
        mock_user_crud.get_by_username = AsyncMock(return_value=MagicMock(id="existing-id"))
        
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        
        with patch('app.endpoints.auth.UserCRUD', return_value=mock_user_crud):
            request = RegisterRequest(
                email="new@example.com",
                username="existinguser",
                password="SecurePass123!"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await register(request, req=mock_request, db=mock_db)
            
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert exc_info.value.detail["code"] == "REGISTRATION_FAILED"
            assert "Unable to complete registration" in exc_info.value.detail["message"]
            assert "details" not in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_registration_duplicate_email_and_username_identical_response(self):
        """Response идентичен для duplicate email и duplicate username"""
        from app.endpoints.auth import register
        from app.schemas.auth import RegisterRequest
        
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        
        email_error_detail = None
        username_error_detail = None
        
        mock_db = AsyncMock()
        mock_user_crud_email = MagicMock()
        mock_user_crud_email.get_by_email = AsyncMock(return_value=MagicMock(id="existing-id"))
        mock_user_crud_email.get_by_username = AsyncMock(return_value=None)
        
        with patch('app.endpoints.auth.UserCRUD', return_value=mock_user_crud_email):
            request = RegisterRequest(
                email="existing@example.com",
                username="newuser",
                password="SecurePass123!"
            )
            
            try:
                await register(request, req=mock_request, db=mock_db)
            except HTTPException as e:
                email_error_detail = e.detail
        
        mock_user_crud_username = MagicMock()
        mock_user_crud_username.get_by_email = AsyncMock(return_value=None)
        mock_user_crud_username.get_by_username = AsyncMock(return_value=MagicMock(id="existing-id"))
        
        with patch('app.endpoints.auth.UserCRUD', return_value=mock_user_crud_username):
            request = RegisterRequest(
                email="new@example.com",
                username="existinguser",
                password="SecurePass123!"
            )
            
            try:
                await register(request, req=mock_request, db=mock_db)
            except HTTPException as e:
                username_error_detail = e.detail
        
        assert email_error_detail == username_error_detail
        assert email_error_detail["code"] == "REGISTRATION_FAILED"

    @pytest.mark.asyncio
    async def test_registration_logs_ip_address(self):
        """IP адрес логируется при ошибке регистрации"""
        from app.endpoints.auth import register
        from app.schemas.auth import RegisterRequest
        
        mock_db = AsyncMock()
        mock_user_crud = MagicMock()
        mock_user_crud.get_by_email = AsyncMock(return_value=MagicMock(id="existing-id"))
        mock_user_crud.get_by_username = AsyncMock(return_value=None)
        
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "10.20.30.40"
        
        with patch('app.endpoints.auth.UserCRUD', return_value=mock_user_crud):
            with patch('app.endpoints.auth.logger') as mock_logger:
                request = RegisterRequest(
                    email="existing@example.com",
                    username="newuser",
                    password="SecurePass123!"
                )
                
                try:
                    await register(request, req=mock_request, db=mock_db)
                except HTTPException:
                    pass
                
                warning_calls = [c for c in mock_logger.warning.call_args_list]
                assert len(warning_calls) > 0
                logged_data = str(warning_calls[0])
                assert "10.20.30.40" in logged_data or "ip_address" in logged_data


class TestVerificationGenericErrors:
    """Тесты для проверки generic error messages при верификации"""

    @pytest.mark.asyncio
    async def test_verification_invalid_code_no_remaining_attempts(self):
        """При неверном коде НЕ возвращается remaining_attempts"""
        from app.endpoints.auth import verify_email
        from app.schemas.auth import VerifyEmailRequest
        
        mock_db = AsyncMock()
        mock_email_crud = MagicMock()
        mock_email_crud.get_valid_code = AsyncMock(return_value=None)
        mock_email_crud.get_by_email = AsyncMock(return_value=MagicMock(attempts=0))
        mock_email_crud.increment_attempts = AsyncMock()
        
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        
        with patch('app.endpoints.auth.EmailVerificationCodeCRUD', return_value=mock_email_crud):
            request = VerifyEmailRequest(
                email="test@example.com",
                code="123456"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_email(request, req=mock_request, db=mock_db)
            
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert exc_info.value.detail["code"] == "INVALID_CODE"
            assert "remaining_attempts" not in exc_info.value.detail
            assert "details" not in exc_info.value.detail

    @pytest.mark.asyncio
    async def test_verification_third_attempt_returns_code_expired(self):
        """После 3-й попытки возвращается VERIFICATION_CODE_EXPIRED"""
        from app.endpoints.auth import verify_email
        from app.schemas.auth import VerifyEmailRequest
        
        mock_db = AsyncMock()
        mock_email_crud = MagicMock()
        mock_email_crud.get_valid_code = AsyncMock(return_value=None)
        mock_email_crud.get_by_email = AsyncMock(return_value=MagicMock(attempts=2))
        mock_email_crud.increment_attempts = AsyncMock()
        mock_email_crud.delete_by_email = AsyncMock()
        
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        
        with patch('app.endpoints.auth.EmailVerificationCodeCRUD', return_value=mock_email_crud):
            request = VerifyEmailRequest(
                email="test@example.com",
                code="123456"
            )
            
            with pytest.raises(HTTPException) as exc_info:
                await verify_email(request, req=mock_request, db=mock_db)
            
            assert exc_info.value.status_code == status.HTTP_400_BAD_REQUEST
            assert exc_info.value.detail["code"] == "VERIFICATION_CODE_EXPIRED"
            assert "Too many attempts" in exc_info.value.detail["message"]
            mock_email_crud.delete_by_email.assert_called_once()

    @pytest.mark.asyncio
    async def test_verification_logs_remaining_attempts_on_server(self):
        """remaining_attempts логируется на сервере, но не возвращается клиенту"""
        from app.endpoints.auth import verify_email
        from app.schemas.auth import VerifyEmailRequest
        
        mock_db = AsyncMock()
        mock_email_crud = MagicMock()
        mock_email_crud.get_valid_code = AsyncMock(return_value=None)
        mock_email_crud.get_by_email = AsyncMock(return_value=MagicMock(attempts=1))
        mock_email_crud.increment_attempts = AsyncMock()
        
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "192.168.1.1"
        
        with patch('app.endpoints.auth.EmailVerificationCodeCRUD', return_value=mock_email_crud):
            with patch('app.endpoints.auth.logger') as mock_logger:
                request = VerifyEmailRequest(
                    email="test@example.com",
                    code="123456"
                )
                
                try:
                    await verify_email(request, req=mock_request, db=mock_db)
                except HTTPException as e:
                    assert "remaining_attempts" not in e.detail
                
                warning_calls = [c for c in mock_logger.warning.call_args_list]
                assert len(warning_calls) > 0
                logged_data = str(warning_calls[0])
                assert "remaining_attempts" in logged_data

    @pytest.mark.asyncio
    async def test_verification_logs_ip_address(self):
        """IP адрес логируется при ошибке верификации"""
        from app.endpoints.auth import verify_email
        from app.schemas.auth import VerifyEmailRequest
        
        mock_db = AsyncMock()
        mock_email_crud = MagicMock()
        mock_email_crud.get_valid_code = AsyncMock(return_value=None)
        mock_email_crud.get_by_email = AsyncMock(return_value=MagicMock(attempts=0))
        mock_email_crud.increment_attempts = AsyncMock()
        
        mock_request = MagicMock(spec=Request)
        mock_request.client = MagicMock()
        mock_request.client.host = "50.60.70.80"
        
        with patch('app.endpoints.auth.EmailVerificationCodeCRUD', return_value=mock_email_crud):
            with patch('app.endpoints.auth.logger') as mock_logger:
                request = VerifyEmailRequest(
                    email="test@example.com",
                    code="123456"
                )
                
                try:
                    await verify_email(request, req=mock_request, db=mock_db)
                except HTTPException:
                    pass
                
                warning_calls = [c for c in mock_logger.warning.call_args_list]
                assert len(warning_calls) > 0
                logged_data = str(warning_calls[0])
                assert "50.60.70.80" in logged_data or "ip_address" in logged_data
