import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.rate_limiter import (
    init_rate_limiter,
    get_client_ip,
    RateLimitExceededError,
)


@pytest.fixture
def mock_settings():
    with patch("app.core.rate_limiter.settings") as mock:
        mock.RATE_LIMIT_ENABLED = True
        mock.REDIS_URL = "redis://localhost:6379/0"
        yield mock


@pytest.fixture
def mock_app():
    return MagicMock()


@pytest.fixture
def mock_request():
    request = MagicMock()
    request.headers = {}
    request.client = MagicMock()
    request.client.host = "192.168.1.1"
    return request


@pytest.mark.asyncio
async def test_init_rate_limiter_success(mock_app, mock_settings):
    mock_redis = AsyncMock()
    
    with patch("app.core.rate_limiter.redis") as mock_redis_module:
        mock_redis_module.from_url.return_value = mock_redis
        
        with patch("app.core.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.init = AsyncMock()
            
            await init_rate_limiter(mock_app)
            
            mock_limiter.init.assert_called_once_with(mock_redis)


@pytest.mark.asyncio
async def test_init_rate_limiter_disabled(mock_app):
    with patch("app.core.rate_limiter.settings") as mock_settings:
        mock_settings.RATE_LIMIT_ENABLED = False
        
        result = await init_rate_limiter(mock_app)
        
        assert result is None


@pytest.mark.asyncio
async def test_init_rate_limiter_redis_error(mock_app, mock_settings):
    with patch("app.core.rate_limiter.redis") as mock_redis_module:
        mock_redis_module.from_url.side_effect = Exception("Redis connection failed")
        
        with pytest.raises(Exception) as exc_info:
            await init_rate_limiter(mock_app)
        
        assert "Redis connection failed" in str(exc_info.value)


def test_get_client_ip_direct(mock_request):
    result = get_client_ip(mock_request)
    
    assert result == "192.168.1.1"


def test_get_client_ip_from_x_forwarded_for(mock_request):
    mock_request.headers = {"X-Forwarded-For": "10.0.0.1, 192.168.1.100"}
    
    result = get_client_ip(mock_request)
    
    assert result == "10.0.0.1"


def test_get_client_ip_x_forwarded_for_with_spaces(mock_request):
    mock_request.headers = {"X-Forwarded-For": "  10.0.0.1 ,  192.168.1.100  "}
    
    result = get_client_ip(mock_request)
    
    assert result == "10.0.0.1"


def test_get_client_ip_no_client(mock_request):
    mock_request.client = None
    
    result = get_client_ip(mock_request)
    
    assert result == "unknown"


def test_get_client_ip_empty_x_forwarded_for(mock_request):
    mock_request.headers = {"X-Forwarded-For": ""}
    
    result = get_client_ip(mock_request)
    
    assert result == "192.168.1.1"


def test_rate_limit_exceeded_error():
    error = RateLimitExceededError(
        retry_after=60,
        limit="5/minute",
        endpoint="/api/v1/auth/login"
    )
    
    assert error.retry_after == 60
    assert error.limit == "5/minute"
    assert error.endpoint == "/api/v1/auth/login"
    assert "Rate limit exceeded" in str(error)


def test_rate_limit_exceeded_error_message():
    error = RateLimitExceededError(
        retry_after=45,
        limit="10/hour",
        endpoint="/api/v1/auth/register"
    )
    
    assert "register" in str(error)


@pytest.mark.asyncio
async def test_init_rate_limiter_with_valid_redis_url(mock_app, mock_settings):
    mock_redis = AsyncMock()
    
    with patch("app.core.rate_limiter.redis") as mock_redis_module:
        mock_redis_module.from_url.return_value = mock_redis
        
        with patch("app.core.rate_limiter.FastAPILimiter") as mock_limiter:
            mock_limiter.init = AsyncMock()
            
            await init_rate_limiter(mock_app)
            
            mock_redis_module.from_url.assert_called_once_with(
                mock_settings.REDIS_URL,
                encoding="utf-8",
                decode_responses=True
            )


def test_get_client_ip_single_forwarded_for(mock_request):
    mock_request.headers = {"X-Forwarded-For": "203.0.113.50"}
    
    result = get_client_ip(mock_request)
    
    assert result == "203.0.113.50"


def test_get_client_ip_ipv6(mock_request):
    mock_request.client.host = "2001:0db8:85a3:0000:0000:8a2e:0370:7334"
    
    result = get_client_ip(mock_request)
    
    assert result == "2001:0db8:85a3:0000:0000:8a2e:0370:7334"


def test_get_client_ip_ipv6_forwarded(mock_request):
    mock_request.headers = {"X-Forwarded-For": "2001:db8::1, 2001:db8::2"}
    
    result = get_client_ip(mock_request)
    
    assert result == "2001:db8::1"
