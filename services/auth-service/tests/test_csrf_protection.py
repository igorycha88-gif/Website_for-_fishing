import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
import os
import redis

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.csrf_protection import CSRFProtection


@pytest.fixture
def mock_redis():
    return AsyncMock()


@pytest.fixture
def csrf_protection(mock_redis):
    protection = CSRFProtection(redis_client=mock_redis)
    protection.ttl = 86400
    return protection


@pytest.mark.asyncio
async def test_generate_token_success(csrf_protection, mock_redis):
    user_id = "test-user-123"
    
    mock_redis.setex.return_value = True
    
    token = await csrf_protection.generate_token(user_id)
    
    assert token is not None
    assert len(token) == 43
    
    mock_redis.setex.assert_called_once()
    call_args = mock_redis.setex.call_args
    assert call_args[0][0] == f"csrf:{user_id}"
    assert call_args[0][1] == 86400
    assert call_args[0][2] == token


@pytest.mark.asyncio
async def test_validate_token_valid(csrf_protection, mock_redis):
    user_id = "test-user-123"
    token = "valid-csrf-token-1234567890123456789012345"
    
    mock_redis.get.return_value = token.encode()
    
    result = await csrf_protection.validate_token(user_id, token)
    
    assert result is True
    mock_redis.get.assert_called_once_with(f"csrf:{user_id}")


@pytest.mark.asyncio
async def test_validate_token_invalid(csrf_protection, mock_redis):
    user_id = "test-user-123"
    stored_token = "stored-token-123456789012345678901234567"
    provided_token = "different-token-12345678901234567890123"
    
    mock_redis.get.return_value = stored_token.encode()
    
    result = await csrf_protection.validate_token(user_id, provided_token)
    
    assert result is False
    mock_redis.get.assert_called_once_with(f"csrf:{user_id}")


@pytest.mark.asyncio
async def test_validate_token_missing(csrf_protection, mock_redis):
    user_id = "test-user-123"
    
    result = await csrf_protection.validate_token(user_id, "")
    
    assert result is False
    mock_redis.get.assert_not_called()


@pytest.mark.asyncio
async def test_validate_token_not_found_in_redis(csrf_protection, mock_redis):
    user_id = "test-user-123"
    token = "some-token-1234567890123456789012345678"
    
    mock_redis.get.return_value = None
    
    result = await csrf_protection.validate_token(user_id, token)
    
    assert result is False
    mock_redis.get.assert_called_once_with(f"csrf:{user_id}")


@pytest.mark.asyncio
async def test_validate_token_redis_unavailable_graceful_degradation(csrf_protection, mock_redis):
    user_id = "test-user-123"
    token = "some-token-1234567890123456789012345678"
    
    mock_redis.get.side_effect = redis.RedisError("Connection refused")
    
    result = await csrf_protection.validate_token(user_id, token)
    
    assert result is True


@pytest.mark.asyncio
async def test_invalidate_token_success(csrf_protection, mock_redis):
    user_id = "test-user-123"
    
    mock_redis.delete.return_value = 1
    
    result = await csrf_protection.invalidate_token(user_id)
    
    assert result is True
    mock_redis.delete.assert_called_once_with(f"csrf:{user_id}")


@pytest.mark.asyncio
async def test_invalidate_token_not_found(csrf_protection, mock_redis):
    user_id = "test-user-123"
    
    mock_redis.delete.return_value = 0
    
    result = await csrf_protection.invalidate_token(user_id)
    
    assert result is False
    mock_redis.delete.assert_called_once_with(f"csrf:{user_id}")


@pytest.mark.asyncio
async def test_invalidate_token_redis_error(csrf_protection, mock_redis):
    user_id = "test-user-123"
    
    mock_redis.delete.side_effect = redis.RedisError("Connection refused")
    
    result = await csrf_protection.invalidate_token(user_id)
    
    assert result is False


@pytest.mark.asyncio
async def test_refresh_token(csrf_protection, mock_redis):
    user_id = "test-user-123"
    
    mock_redis.delete.return_value = 1
    mock_redis.setex.return_value = True
    
    new_token = await csrf_protection.refresh_token(user_id)
    
    assert new_token is not None
    assert len(new_token) == 43
    
    mock_redis.delete.assert_called_once_with(f"csrf:{user_id}")
    mock_redis.setex.assert_called_once()


@pytest.mark.asyncio
async def test_validate_token_with_string_value(csrf_protection, mock_redis):
    user_id = "test-user-123"
    token = "valid-csrf-token-1234567890123456789012345"
    
    mock_redis.get.return_value = token
    
    result = await csrf_protection.validate_token(user_id, token)
    
    assert result is True


@pytest.mark.asyncio
async def test_token_is_43_chars(csrf_protection, mock_redis):
    user_id = "test-user-123"
    
    mock_redis.setex.return_value = True
    
    token = await csrf_protection.generate_token(user_id)
    
    assert len(token) == 43
    import re
    assert re.match(r'^[A-Za-z0-9_-]+$', token), "Token should be URL-safe base64"
