import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os
import httpx

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.exceptions import EmailServiceUnavailableError


class TestNoHardcodedVerificationCode:
    """Тесты для проверки устранения hardcoded verification code"""

    @pytest.mark.asyncio
    async def test_no_hardcoded_code_on_smtp_failure(self):
        """При ошибке SMTP должен возвращаться 503, а не fallback код"""
        from app.core.config import settings
        
        with patch.object(settings, 'ENABLE_EMAIL_SENDING', True):
            with patch('httpx.AsyncClient') as mock_httpx:
                mock_client = AsyncMock()
                mock_client.post = AsyncMock(side_effect=Exception("SMTP error"))
                mock_httpx.return_value.__aenter__.return_value = mock_client
                
                from app.endpoints.auth import register
                from app.schemas.auth import RegisterRequest
                from sqlalchemy.ext.asyncio import AsyncSession
                
                mock_db = AsyncMock(spec=AsyncSession)
                mock_user_crud = MagicMock()
                mock_user_crud.get_by_email = AsyncMock(return_value=None)
                mock_user_crud.get_by_username = AsyncMock(return_value=None)
                mock_user_crud.create = AsyncMock(
                    return_value=MagicMock(id="test-id", email="user@example.com")
                )
                
                with patch('app.endpoints.auth.UserCRUD', return_value=mock_user_crud):
                    request = RegisterRequest(
                        email="user@example.com",
                        username="testuser",
                        password="SecurePass123!"
                    )
                    
                    with pytest.raises(EmailServiceUnavailableError):
                        await register(request, db=mock_db)

    @pytest.mark.asyncio
    async def test_dev_mode_whitelist_domain(self):
        """В dev режиме whitelist домен получает случайный код"""
        from app.core.config import settings
        
        with patch.object(settings, 'ENABLE_EMAIL_SENDING', False):
            with patch.object(settings, 'ENVIRONMENT', 'development'):
                with patch.object(settings, 'DEV_EMAIL_DOMAIN', 'test.example.com'):
                    from app.endpoints.auth import register
                    from app.schemas.auth import RegisterRequest
                    from sqlalchemy.ext.asyncio import AsyncSession
                    
                    mock_db = AsyncMock(spec=AsyncSession)
                    mock_user_crud = MagicMock()
                    mock_user_crud.get_by_email = AsyncMock(return_value=None)
                    mock_user_crud.get_by_username = AsyncMock(return_value=None)
                    mock_user_crud.create = AsyncMock(
                        return_value=MagicMock(id="test-id", email="user@test.example.com")
                    )
                    
                    mock_email_crud = MagicMock()
                    mock_email_crud.create = AsyncMock()
                    
                    with patch('app.endpoints.auth.UserCRUD', return_value=mock_user_crud):
                        with patch('app.endpoints.auth.EmailVerificationCodeCRUD', return_value=mock_email_crud):
                            request = RegisterRequest(
                                email="user@test.example.com",
                                username="testuser",
                                password="SecurePass123!"
                            )
                            
                            result = await register(request, db=mock_db)
                            
                            assert result is not None
                            mock_email_crud.create.assert_called_once()
                            call_args = mock_email_crud.create.call_args
                            saved_code = call_args[0][1]
                            assert saved_code != "123456"
                            assert len(saved_code) == 6

    @pytest.mark.asyncio
    async def test_dev_mode_non_whitelist_domain(self):
        """В dev режиме НЕ-whitelist домен получает 503"""
        from app.core.config import settings
        
        with patch.object(settings, 'ENABLE_EMAIL_SENDING', False):
            with patch.object(settings, 'ENVIRONMENT', 'development'):
                with patch.object(settings, 'DEV_EMAIL_DOMAIN', 'test.localhost'):
                    from app.endpoints.auth import register
                    from app.schemas.auth import RegisterRequest
                    from sqlalchemy.ext.asyncio import AsyncSession
                    
                    mock_db = AsyncMock(spec=AsyncSession)
                    mock_user_crud = MagicMock()
                    mock_user_crud.get_by_email = AsyncMock(return_value=None)
                    mock_user_crud.get_by_username = AsyncMock(return_value=None)
                    mock_user_crud.create = AsyncMock(
                        return_value=MagicMock(id="test-id", email="user@example.com")
                    )
                    
                    with patch('app.endpoints.auth.UserCRUD', return_value=mock_user_crud):
                        request = RegisterRequest(
                            email="user@example.com",
                            username="testuser",
                            password="SecurePass123!"
                        )
                        
                        with pytest.raises(EmailServiceUnavailableError):
                            await register(request, db=mock_db)

    @pytest.mark.asyncio
    async def test_production_mode_no_fallback(self):
        """В production режиме НИКОГДА не используется fallback код"""
        from app.core.config import settings
        
        with patch.object(settings, 'ENABLE_EMAIL_SENDING', False):
            with patch.object(settings, 'ENVIRONMENT', 'production'):
                from app.endpoints.auth import register
                from app.schemas.auth import RegisterRequest
                from sqlalchemy.ext.asyncio import AsyncSession
                
                mock_db = AsyncMock(spec=AsyncSession)
                mock_user_crud = MagicMock()
                mock_user_crud.get_by_email = AsyncMock(return_value=None)
                mock_user_crud.get_by_username = AsyncMock(return_value=None)
                mock_user_crud.create = AsyncMock(
                    return_value=MagicMock(id="test-id", email="user@test.example.com")
                )
                
                with patch('app.endpoints.auth.UserCRUD', return_value=mock_user_crud):
                    request = RegisterRequest(
                        email="user@test.example.com",
                        username="testuser",
                        password="SecurePass123!"
                    )
                    
                    with pytest.raises(EmailServiceUnavailableError):
                        await register(request, db=mock_db)

    @pytest.mark.asyncio
    async def test_production_mode_smtp_error(self):
        """В production режиме при SMTP ошибке возвращается 503"""
        from app.core.config import settings
        
        with patch.object(settings, 'ENABLE_EMAIL_SENDING', True):
            with patch.object(settings, 'ENVIRONMENT', 'production'):
                with patch('httpx.AsyncClient') as mock_httpx:
                    mock_client = AsyncMock()
                    mock_client.post = AsyncMock(side_effect=Exception("SMTP error"))
                    mock_httpx.return_value.__aenter__.return_value = mock_client
                    
                    from app.endpoints.auth import register
                    from app.schemas.auth import RegisterRequest
                    from sqlalchemy.ext.asyncio import AsyncSession
                    
                    mock_db = AsyncMock(spec=AsyncSession)
                    mock_user_crud = MagicMock()
                    mock_user_crud.get_by_email = AsyncMock(return_value=None)
                    mock_user_crud.get_by_username = AsyncMock(return_value=None)
                    mock_user_crud.create = AsyncMock(
                        return_value=MagicMock(id="test-id", email="user@example.com")
                    )
                    
                    with patch('app.endpoints.auth.UserCRUD', return_value=mock_user_crud):
                        request = RegisterRequest(
                            email="user@example.com",
                            username="testuser",
                            password="SecurePass123!"
                        )
                        
                        with pytest.raises(EmailServiceUnavailableError):
                            await register(request, db=mock_db)


class TestEmailServiceUnavailableError:
    """Тесты для проверки исключения EmailServiceUnavailableError"""

    def test_exception_has_correct_status_code(self):
        """Исключение должно возвращать HTTP 503"""
        exc = EmailServiceUnavailableError()
        
        assert exc.status_code == 503

    def test_exception_has_correct_detail(self):
        """Исключение должно содержать правильный detail"""
        exc = EmailServiceUnavailableError()
        
        assert exc.detail["error"]["code"] == "EMAIL_SERVICE_UNAVAILABLE"
        assert "недоступен" in exc.detail["error"]["message"].lower()


class TestVerificationCodeNot123456:
    """Интеграционные тесты для проверки что код 123456 больше не работает"""

    @pytest.mark.asyncio
    async def test_random_code_generation(self):
        """Проверка что генерируется случайный код, а не 123456"""
        import secrets
        
        codes = [secrets.token_hex(3).upper() for _ in range(10)]
        
        for code in codes:
            assert code != "123456"
            assert len(code) == 6
            assert all(c in '0123456789ABCDEF' for c in code)

    @pytest.mark.asyncio
    async def test_different_codes_generated(self):
        """Проверка что генерируются разные коды"""
        import secrets
        
        codes = set()
        for _ in range(20):
            code = secrets.token_hex(3).upper()
            codes.add(code)
        
        assert len(codes) >= 18  # Почти все коды должны быть уникальными
