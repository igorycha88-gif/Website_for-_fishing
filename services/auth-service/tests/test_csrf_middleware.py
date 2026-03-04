"""
Tests for CSRFMiddleware.

CRITICAL BUG FIXED:
  Previously the middleware used `raise HTTPException(...)` which bypasses
  FastAPI's ExceptionMiddleware (which sits *inside* the middleware stack) and
  reaches Starlette's ServerErrorMiddleware — converting any exception into
  HTTP 500. This caused `PUT /api/v1/users/me` to return 500 instead of 403
  when the CSRF token was missing.

  Fix: all error responses are now returned as `JSONResponse` objects directly.

Test approach: dispatch() is called with mock Request/call_next objects.
  We assert on the returned Response object (status_code + body) rather than
  on raised exceptions, since the fix means no exceptions are raised any more.
"""
import json
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from fastapi.responses import JSONResponse
from app.middleware.csrf import CSRFMiddleware


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def mock_app():
    return MagicMock()


@pytest.fixture
def mock_csrf_protection():
    protection = AsyncMock()
    protection.validate_token = AsyncMock(return_value=True)
    protection.invalidate_token = AsyncMock(return_value=True)
    return protection


@pytest.fixture
def csrf_middleware(mock_app):
    return CSRFMiddleware(mock_app)


def _make_request(
    method: str = "PUT",
    path: str = "/api/v1/users/me",
    auth_header: str | None = "Bearer valid_token",
    csrf_header: str | None = None,
    scope_type: str = "http",
) -> MagicMock:
    """Build a minimal mock Request."""

    def _get_header(name: str):
        mapping = {}
        if auth_header is not None:
            mapping["Authorization"] = auth_header
        if csrf_header is not None:
            mapping["X-CSRF-Token"] = csrf_header
        return mapping.get(name)

    req = MagicMock()
    req.scope = {"type": scope_type}
    req.method = method
    req.url.path = path
    req.headers.get = MagicMock(side_effect=_get_header)
    req.client.host = "127.0.0.1"
    return req


def _parse_body(response) -> dict:
    """Parse JSONResponse body."""
    if hasattr(response, "body"):
        return json.loads(response.body)
    return {}


# ---------------------------------------------------------------------------
# Tests: middleware configuration
# ---------------------------------------------------------------------------


def test_protected_methods_set(csrf_middleware):
    assert csrf_middleware.protected_methods == {"POST", "PUT", "DELETE", "PATCH"}


def test_skip_paths_set(csrf_middleware):
    assert "/api/v1/auth/login" in csrf_middleware.skip_paths
    assert "/api/v1/auth/register" in csrf_middleware.skip_paths
    assert "/api/v1/auth/verify-email" in csrf_middleware.skip_paths
    assert "/api/v1/auth/reset-password/request" in csrf_middleware.skip_paths
    assert "/api/v1/auth/reset-password/confirm" in csrf_middleware.skip_paths
    assert "/api/v1/auth/refresh" in csrf_middleware.skip_paths


def test_get_not_in_protected_methods(csrf_middleware):
    assert "GET" not in csrf_middleware.protected_methods
    assert "OPTIONS" not in csrf_middleware.protected_methods
    assert "HEAD" not in csrf_middleware.protected_methods


# ---------------------------------------------------------------------------
# Tests: requests that must be skipped (call_next called, no validation)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_skips_non_http_scope(csrf_middleware):
    req = _make_request(scope_type="websocket")
    call_next = AsyncMock()
    await csrf_middleware.dispatch(req, call_next)
    call_next.assert_called_once_with(req)


@pytest.mark.asyncio
async def test_skips_get_requests(csrf_middleware):
    req = _make_request(method="GET")
    call_next = AsyncMock()
    await csrf_middleware.dispatch(req, call_next)
    call_next.assert_called_once_with(req)


@pytest.mark.asyncio
async def test_skips_options_requests(csrf_middleware):
    req = _make_request(method="OPTIONS")
    call_next = AsyncMock()
    await csrf_middleware.dispatch(req, call_next)
    call_next.assert_called_once_with(req)


@pytest.mark.asyncio
async def test_skips_login_path(csrf_middleware):
    req = _make_request(method="POST", path="/api/v1/auth/login")
    call_next = AsyncMock()
    with patch("app.middleware.csrf.settings") as s:
        s.CSRF_ENABLED = True
        await csrf_middleware.dispatch(req, call_next)
    call_next.assert_called_once_with(req)


@pytest.mark.asyncio
async def test_skips_register_path(csrf_middleware):
    req = _make_request(method="POST", path="/api/v1/auth/register")
    call_next = AsyncMock()
    with patch("app.middleware.csrf.settings") as s:
        s.CSRF_ENABLED = True
        await csrf_middleware.dispatch(req, call_next)
    call_next.assert_called_once_with(req)


@pytest.mark.asyncio
async def test_skips_verify_email_path(csrf_middleware):
    req = _make_request(method="POST", path="/api/v1/auth/verify-email")
    call_next = AsyncMock()
    with patch("app.middleware.csrf.settings") as s:
        s.CSRF_ENABLED = True
        await csrf_middleware.dispatch(req, call_next)
    call_next.assert_called_once_with(req)


@pytest.mark.asyncio
async def test_skips_refresh_path(csrf_middleware):
    req = _make_request(method="POST", path="/api/v1/auth/refresh")
    call_next = AsyncMock()
    with patch("app.middleware.csrf.settings") as s:
        s.CSRF_ENABLED = True
        await csrf_middleware.dispatch(req, call_next)
    call_next.assert_called_once_with(req)


@pytest.mark.asyncio
async def test_skips_when_csrf_disabled(csrf_middleware):
    req = _make_request()
    call_next = AsyncMock()
    with patch("app.middleware.csrf.settings") as s:
        s.CSRF_ENABLED = False
        await csrf_middleware.dispatch(req, call_next)
    call_next.assert_called_once_with(req)


@pytest.mark.asyncio
async def test_skips_when_no_auth_header(csrf_middleware):
    req = _make_request(auth_header=None)
    call_next = AsyncMock()
    with patch("app.middleware.csrf.settings") as s:
        s.CSRF_ENABLED = True
        await csrf_middleware.dispatch(req, call_next)
    call_next.assert_called_once_with(req)


@pytest.mark.asyncio
async def test_skips_when_auth_header_not_bearer(csrf_middleware):
    req = _make_request(auth_header="Basic dXNlcjpwYXNz")
    call_next = AsyncMock()
    with patch("app.middleware.csrf.settings") as s:
        s.CSRF_ENABLED = True
        await csrf_middleware.dispatch(req, call_next)
    call_next.assert_called_once_with(req)


# ---------------------------------------------------------------------------
# CRITICAL REGRESSION TEST
# Previously: raise HTTPException(403) → ServerErrorMiddleware → 500
# After fix:  return JSONResponse(403) → client gets 403
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_missing_csrf_token_returns_json_response_403():
    """
    THE PRIMARY REGRESSION TEST.

    When X-CSRF-Token is absent the middleware must return a JSONResponse with
    status 403 — NOT raise an HTTPException that leaks to ServerErrorMiddleware
    and becomes HTTP 500.
    """
    app = MagicMock()
    middleware = CSRFMiddleware(app)
    req = _make_request(csrf_header=None)
    call_next = AsyncMock()

    with (
        patch("app.middleware.csrf.settings") as s,
        patch(
            "app.middleware.csrf.decode_access_token",
            return_value={"sub": "user-uuid"},
        ),
    ):
        s.CSRF_ENABLED = True
        result = await middleware.dispatch(req, call_next)

    # Must be a JSONResponse, not a raised exception
    assert isinstance(result, JSONResponse), (
        f"Expected JSONResponse, got {type(result)}. "
        "HTTPException must NOT be raised inside BaseHTTPMiddleware."
    )
    assert result.status_code == 403, (
        f"Expected status 403, got {result.status_code}"
    )
    body = _parse_body(result)
    assert body.get("detail", {}).get("code") == "CSRF_TOKEN_MISSING", (
        f"Unexpected body: {body}"
    )
    # call_next must NOT have been called
    call_next.assert_not_called()


@pytest.mark.asyncio
async def test_missing_csrf_token_message():
    """Response body must contain a human-readable message."""
    app = MagicMock()
    middleware = CSRFMiddleware(app)
    req = _make_request(csrf_header=None)
    call_next = AsyncMock()

    with (
        patch("app.middleware.csrf.settings") as s,
        patch("app.middleware.csrf.decode_access_token", return_value={"sub": "uid"}),
    ):
        s.CSRF_ENABLED = True
        result = await middleware.dispatch(req, call_next)

    body = _parse_body(result)
    assert "message" in body.get("detail", {}), f"Unexpected body: {body}"


# ---------------------------------------------------------------------------
# Tests: invalid CSRF token — must return 403 CSRF_TOKEN_INVALID
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalid_csrf_token_returns_json_response_403(mock_csrf_protection):
    app = MagicMock()
    middleware = CSRFMiddleware(app)
    req = _make_request(csrf_header="wrong_token")
    call_next = AsyncMock()
    mock_csrf_protection.validate_token = AsyncMock(return_value=False)

    with (
        patch("app.middleware.csrf.settings") as s,
        patch("app.middleware.csrf.decode_access_token", return_value={"sub": "uid"}),
        patch("app.middleware.csrf.get_csrf_protection", return_value=mock_csrf_protection),
    ):
        s.CSRF_ENABLED = True
        result = await middleware.dispatch(req, call_next)

    assert isinstance(result, JSONResponse)
    assert result.status_code == 403
    body = _parse_body(result)
    assert body.get("detail", {}).get("code") == "CSRF_TOKEN_INVALID"
    call_next.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: invalid JWT — must return 401
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_invalid_jwt_returns_json_response_401():
    app = MagicMock()
    middleware = CSRFMiddleware(app)
    req = _make_request()
    call_next = AsyncMock()

    with (
        patch("app.middleware.csrf.settings") as s,
        patch("app.middleware.csrf.decode_access_token", return_value=None),
    ):
        s.CSRF_ENABLED = True
        result = await middleware.dispatch(req, call_next)

    assert isinstance(result, JSONResponse)
    assert result.status_code == 401
    body = _parse_body(result)
    assert body.get("detail", {}).get("code") == "UNAUTHORIZED"
    call_next.assert_not_called()


@pytest.mark.asyncio
async def test_jwt_without_sub_returns_401():
    app = MagicMock()
    middleware = CSRFMiddleware(app)
    req = _make_request()
    call_next = AsyncMock()

    with (
        patch("app.middleware.csrf.settings") as s,
        # Token decoded but has no "sub" field
        patch("app.middleware.csrf.decode_access_token", return_value={"jti": "abc"}),
    ):
        s.CSRF_ENABLED = True
        result = await middleware.dispatch(req, call_next)

    assert isinstance(result, JSONResponse)
    assert result.status_code == 401
    call_next.assert_not_called()


# ---------------------------------------------------------------------------
# Tests: valid CSRF token — request passes through to call_next
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_valid_csrf_token_calls_call_next(mock_csrf_protection):
    app = MagicMock()
    middleware = CSRFMiddleware(app)
    req = _make_request(csrf_header="correct_csrf_token")
    call_next = AsyncMock(return_value=MagicMock(status_code=200))
    mock_csrf_protection.validate_token = AsyncMock(return_value=True)

    with (
        patch("app.middleware.csrf.settings") as s,
        patch("app.middleware.csrf.decode_access_token", return_value={"sub": "uid"}),
        patch("app.middleware.csrf.get_csrf_protection", return_value=mock_csrf_protection),
    ):
        s.CSRF_ENABLED = True
        await middleware.dispatch(req, call_next)

    call_next.assert_called_once_with(req)
    mock_csrf_protection.validate_token.assert_called_once_with(
        "uid", "correct_csrf_token"
    )


# ---------------------------------------------------------------------------
# Tests: CSRF not initialized (Redis down) — graceful degradation
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_csrf_not_initialized_lets_request_through():
    """
    When get_csrf_protection() raises RuntimeError (Redis unavailable at startup),
    the middleware must skip validation and call call_next — not return 500.
    """
    app = MagicMock()
    middleware = CSRFMiddleware(app)
    req = _make_request(csrf_header="any_token")
    call_next = AsyncMock(return_value=MagicMock(status_code=200))

    with (
        patch("app.middleware.csrf.settings") as s,
        patch("app.middleware.csrf.decode_access_token", return_value={"sub": "uid"}),
        patch(
            "app.middleware.csrf.get_csrf_protection",
            side_effect=RuntimeError("CSRF protection not initialized"),
        ),
    ):
        s.CSRF_ENABLED = True
        await middleware.dispatch(req, call_next)

    call_next.assert_called_once_with(req)


# ---------------------------------------------------------------------------
# Tests: unexpected exception — must return 500 JSONResponse (not raise)
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_unexpected_exception_returns_json_500():
    """
    If an unexpected error occurs inside the middleware's try block, it must
    return a JSONResponse(500) with a structured body — not propagate the
    exception to ServerErrorMiddleware.
    """
    app = MagicMock()
    middleware = CSRFMiddleware(app)
    req = _make_request()
    call_next = AsyncMock()

    with (
        patch("app.middleware.csrf.settings") as s,
        patch(
            "app.middleware.csrf.decode_access_token",
            side_effect=RuntimeError("unexpected error"),
        ),
    ):
        s.CSRF_ENABLED = True
        result = await middleware.dispatch(req, call_next)

    assert isinstance(result, JSONResponse)
    assert result.status_code == 500
    body = _parse_body(result)
    assert body.get("detail", {}).get("code") == "INTERNAL_ERROR"
