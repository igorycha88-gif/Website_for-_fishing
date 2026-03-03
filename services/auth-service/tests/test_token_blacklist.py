import pytest
from unittest.mock import AsyncMock, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.token_blacklist import TokenBlacklist


@pytest.fixture
def mock_redis():
    return AsyncMock()


@pytest.fixture
def token_blacklist(mock_redis):
    return TokenBlacklist(redis_client=mock_redis)


@pytest.mark.asyncio
async def test_add_access_token_success(token_blacklist, mock_redis):
    jti = "test-jti-123"
    expires_in_seconds = 1800
    
    mock_redis.setex.return_value = True
    
    result = await token_blacklist.add_access_token(jti, expires_in_seconds)
    
    assert result is True
    mock_redis.setex.assert_called_once_with(
        f"blacklist:access:{jti}",
        expires_in_seconds,
        "1"
    )


@pytest.mark.asyncio
async def test_add_refresh_token_success(token_blacklist, mock_redis):
    jti = "test-jti-456"
    expires_in_seconds = 604800
    
    mock_redis.setex.return_value = True
    
    result = await token_blacklist.add_refresh_token(jti, expires_in_seconds)
    
    assert result is True
    mock_redis.setex.assert_called_once_with(
        f"blacklist:refresh:{jti}",
        expires_in_seconds,
        "1"
    )


@pytest.mark.asyncio
async def test_is_access_token_revoked_true(token_blacklist, mock_redis):
    jti = "revoked-jti"
    
    mock_redis.exists.return_value = 1
    
    result = await token_blacklist.is_access_token_revoked(jti)
    
    assert result is True
    mock_redis.exists.assert_called_once_with(f"blacklist:access:{jti}")


@pytest.mark.asyncio
async def test_is_access_token_revoked_false(token_blacklist, mock_redis):
    jti = "valid-jti"
    
    mock_redis.exists.return_value = 0
    
    result = await token_blacklist.is_access_token_revoked(jti)
    
    assert result is False
    mock_redis.exists.assert_called_once_with(f"blacklist:access:{jti}")


@pytest.mark.asyncio
async def test_is_refresh_token_revoked_true(token_blacklist, mock_redis):
    jti = "revoked-refresh-jti"
    
    mock_redis.exists.return_value = 1
    
    result = await token_blacklist.is_refresh_token_revoked(jti)
    
    assert result is True
    mock_redis.exists.assert_called_once_with(f"blacklist:refresh:{jti}")


@pytest.mark.asyncio
async def test_is_refresh_token_revoked_false(token_blacklist, mock_redis):
    jti = "valid-refresh-jti"
    
    mock_redis.exists.return_value = 0
    
    result = await token_blacklist.is_refresh_token_revoked(jti)
    
    assert result is False
    mock_redis.exists.assert_called_once_with(f"blacklist:refresh:{jti}")


@pytest.mark.asyncio
async def test_add_access_token_redis_error(token_blacklist, mock_redis):
    jti = "test-jti-error"
    expires_in_seconds = 1800
    
    mock_redis.setex.side_effect = Exception("Redis connection error")
    
    result = await token_blacklist.add_access_token(jti, expires_in_seconds)
    
    assert result is False


@pytest.mark.asyncio
async def test_add_refresh_token_redis_error(token_blacklist, mock_redis):
    jti = "test-jti-error"
    expires_in_seconds = 604800
    
    mock_redis.setex.side_effect = Exception("Redis connection error")
    
    result = await token_blacklist.add_refresh_token(jti, expires_in_seconds)
    
    assert result is False


@pytest.mark.asyncio
async def test_is_access_token_revoked_redis_error_returns_false(token_blacklist, mock_redis):
    jti = "test-jti"
    
    mock_redis.exists.side_effect = Exception("Redis connection error")
    
    result = await token_blacklist.is_access_token_revoked(jti)
    
    assert result is False


@pytest.mark.asyncio
async def test_is_refresh_token_revoked_redis_error_returns_false(token_blacklist, mock_redis):
    jti = "test-jti"
    
    mock_redis.exists.side_effect = Exception("Redis connection error")
    
    result = await token_blacklist.is_refresh_token_revoked(jti)
    
    assert result is False
