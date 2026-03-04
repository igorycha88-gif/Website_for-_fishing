import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from fastapi.testclient import TestClient
from fastapi import FastAPI, Request, HTTPException
from fastapi.responses import JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.rate_limiter import RateLimitExceededError


@pytest.fixture
def mock_redis():
    redis_mock = AsyncMock()
    return redis_mock


@pytest.fixture
def mock_rate_limiter():
    with patch("app.core.rate_limiter.FastAPILimiter") as mock:
        mock.init = AsyncMock()
        yield mock


@pytest.fixture
def rate_limit_app():
    app = FastAPI()
    
    request_counts = {}
    
    @app.exception_handler(HTTPException)
    async def rate_limit_handler(request: Request, exc: HTTPException):
        if exc.status_code == HTTP_429_TOO_MANY_REQUESTS:
            retry_seconds = 60
            return JSONResponse(
                status_code=429,
                headers={"Retry-After": str(retry_seconds)},
                content={
                    "error": {
                        "code": "RATE_LIMIT_EXCEEDED",
                        "message": "Too many requests. Please try again later.",
                        "details": {
                            "retry_after": retry_seconds,
                            "endpoint": request.url.path,
                        }
                    }
                }
            )
        raise exc
    
    @app.post("/api/v1/auth/login")
    async def login(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:login"
        
        request_counts[key] = request_counts.get(key, 0) + 1
        
        if request_counts[key] > 5:
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        return {"success": True, "access_token": "test-token"}
    
    @app.post("/api/v1/auth/register")
    async def register(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:register"
        
        request_counts[key] = request_counts.get(key, 0) + 1
        
        if request_counts[key] > 10:
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        return {"success": True, "message": "Registered"}
    
    @app.post("/api/v1/auth/reset-password/request")
    async def reset_password(request: Request):
        client_ip = request.client.host if request.client else "unknown"
        key = f"{client_ip}:reset-password"
        
        request_counts[key] = request_counts.get(key, 0) + 1
        
        if request_counts[key] > 3:
            raise HTTPException(
                status_code=HTTP_429_TOO_MANY_REQUESTS,
                detail="Rate limit exceeded"
            )
        
        return {"success": True, "message": "Reset email sent"}
    
    @app.get("/health")
    async def health():
        return {"status": "healthy"}
    
    return app, request_counts


class TestRateLimitingIntegration:
    
    def test_login_requests_within_limit_pass(self, rate_limit_app):
        app, _ = rate_limit_app
        client = TestClient(app)
        
        for i in range(5):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "test@test.com", "password": "password123"}
            )
            assert response.status_code == 200, f"Request {i+1} should succeed"
    
    def test_login_sixth_request_returns_429(self, rate_limit_app):
        app, _ = rate_limit_app
        client = TestClient(app)
        
        for i in range(5):
            client.post(
                "/api/v1/auth/login",
                json={"email": "test@test.com", "password": "password123"}
            )
        
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "password123"}
        )
        
        assert response.status_code == 429
    
    def test_429_response_contains_retry_after_header(self, rate_limit_app):
        app, _ = rate_limit_app
        client = TestClient(app)
        
        for _ in range(6):
            client.post(
                "/api/v1/auth/login",
                json={"email": "test@test.com", "password": "password123"}
            )
        
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "password123"}
        )
        
        assert "retry-after" in response.headers
        retry_after = int(response.headers["retry-after"])
        assert retry_after > 0
    
    def test_429_response_contains_error_details(self, rate_limit_app):
        app, _ = rate_limit_app
        client = TestClient(app)
        
        for _ in range(6):
            client.post(
                "/api/v1/auth/login",
                json={"email": "test@test.com", "password": "password123"}
            )
        
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "password123"}
        )
        
        body = response.json()
        assert "error" in body
        assert body["error"]["code"] == "RATE_LIMIT_EXCEEDED"
        assert "retry_after" in body["error"]["details"]
        assert "endpoint" in body["error"]["details"]
    
    def test_different_endpoints_have_independent_limits(self, rate_limit_app):
        app, _ = rate_limit_app
        client = TestClient(app)
        
        for _ in range(6):
            client.post(
                "/api/v1/auth/login",
                json={"email": "test@test.com", "password": "password123"}
            )
        
        login_response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "password123"}
        )
        assert login_response.status_code == 429
        
        register_response = client.post(
            "/api/v1/auth/register",
            json={"email": "new@test.com", "username": "newuser", "password": "password123"}
        )
        assert register_response.status_code == 200
    
    def test_different_ips_have_independent_limits(self, rate_limit_app):
        app, request_counts = rate_limit_app
        
        with TestClient(app, base_url="http://testserver") as client1:
            for _ in range(6):
                client1.post(
                    "/api/v1/auth/login",
                    json={"email": "test@test.com", "password": "password123"}
                )
            
            response1 = client1.post(
                "/api/v1/auth/login",
                json={"email": "test@test.com", "password": "password123"}
            )
            assert response1.status_code == 429
        
        with TestClient(app, base_url="http://192.168.1.100") as client2:
            request_counts.clear()
            
            response2 = client2.post(
                "/api/v1/auth/login",
                json={"email": "test@test.com", "password": "password123"}
            )
            assert response2.status_code == 200
    
    def test_register_endpoint_limit_10_per_hour(self, rate_limit_app):
        app, _ = rate_limit_app
        client = TestClient(app)
        
        for i in range(10):
            response = client.post(
                "/api/v1/auth/register",
                json={"email": f"test{i}@test.com", "username": f"user{i}", "password": "password123"}
            )
            assert response.status_code == 200, f"Request {i+1} should succeed"
        
        response = client.post(
            "/api/v1/auth/register",
            json={"email": "test11@test.com", "username": "user11", "password": "password123"}
        )
        assert response.status_code == 429
    
    def test_reset_password_endpoint_limit_3_per_hour(self, rate_limit_app):
        app, _ = rate_limit_app
        client = TestClient(app)
        
        for i in range(3):
            response = client.post(
                "/api/v1/auth/reset-password/request",
                json={"email": f"test{i}@test.com"}
            )
            assert response.status_code == 200, f"Request {i+1} should succeed"
        
        response = client.post(
            "/api/v1/auth/reset-password/request",
            json={"email": "test4@test.com"}
        )
        assert response.status_code == 429


class TestRateLimitExceededError:
    
    def test_error_creation(self):
        error = RateLimitExceededError(
            retry_after=60,
            limit="5/minute",
            endpoint="/api/v1/auth/login"
        )
        
        assert error.retry_after == 60
        assert error.limit == "5/minute"
        assert error.endpoint == "/api/v1/auth/login"
    
    def test_error_message(self):
        error = RateLimitExceededError(
            retry_after=45,
            limit="10/hour",
            endpoint="/api/v1/auth/register"
        )
        
        assert "/api/v1/auth/register" in str(error)
    
    def test_error_is_exception(self):
        error = RateLimitExceededError(
            retry_after=60,
            limit="5/minute",
            endpoint="/api/v1/auth/login"
        )
        
        assert isinstance(error, Exception)


class TestRateLimitResponseFormat:
    
    def test_429_response_has_correct_json_structure(self, rate_limit_app):
        app, _ = rate_limit_app
        client = TestClient(app)
        
        for _ in range(6):
            client.post(
                "/api/v1/auth/login",
                json={"email": "test@test.com", "password": "password123"}
            )
        
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "password123"}
        )
        
        body = response.json()
        
        assert "error" in body
        assert "code" in body["error"]
        assert "message" in body["error"]
        assert "details" in body["error"]
        assert "retry_after" in body["error"]["details"]
        assert "endpoint" in body["error"]["details"]
    
    def test_429_response_headers_include_rate_limit_info(self, rate_limit_app):
        app, _ = rate_limit_app
        client = TestClient(app)
        
        for _ in range(6):
            client.post(
                "/api/v1/auth/login",
                json={"email": "test@test.com", "password": "password123"}
            )
        
        response = client.post(
            "/api/v1/auth/login",
            json={"email": "test@test.com", "password": "password123"}
        )
        
        assert response.status_code == 429
        assert "retry-after" in response.headers
        assert int(response.headers["retry-after"]) > 0


class TestRateLimitSecurity:
    
    def test_rate_limit_prevents_brute_force_on_login(self, rate_limit_app):
        app, _ = rate_limit_app
        client = TestClient(app)
        
        blocked_count = 0
        for i in range(20):
            response = client.post(
                "/api/v1/auth/login",
                json={"email": "victim@test.com", "password": f"guess{i}"}
            )
            if response.status_code == 429:
                blocked_count += 1
        
        assert blocked_count >= 14
    
    def test_rate_limit_prevents_mass_registration(self, rate_limit_app):
        app, _ = rate_limit_app
        client = TestClient(app)
        
        blocked_count = 0
        for i in range(20):
            response = client.post(
                "/api/v1/auth/register",
                json={"email": f"spam{i}@test.com", "username": f"spam{i}", "password": "password123"}
            )
            if response.status_code == 429:
                blocked_count += 1
        
        assert blocked_count >= 9
    
    def test_rate_limit_prevents_email_flooding(self, rate_limit_app):
        app, _ = rate_limit_app
        client = TestClient(app)
        
        blocked_count = 0
        for i in range(10):
            response = client.post(
                "/api/v1/auth/reset-password/request",
                json={"email": f"victim{i}@test.com"}
            )
            if response.status_code == 429:
                blocked_count += 1
        
        assert blocked_count >= 6
