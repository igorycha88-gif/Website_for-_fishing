from fastapi import Request
from fastapi.responses import JSONResponse
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.security import decode_access_token
from app.core.csrf_protection import get_csrf_protection
from app.core.logging_config import get_logger
from app.core.config import settings

logger = get_logger(__name__)


class CSRFMiddleware(BaseHTTPMiddleware):
    """
    CSRF Protection Middleware.

    Validates CSRF token for all state-changing requests (POST, PUT, DELETE, PATCH).
    Skips CSRF validation for:
    - GET, OPTIONS, HEAD requests
    - Endpoints without authentication (/login, /register, /verify-email, /refresh)

    IMPORTANT: all error responses are returned as JSONResponse objects, NOT
    raised as HTTPException. Raising HTTPException inside BaseHTTPMiddleware
    bypasses FastAPI's ExceptionMiddleware (which sits *inside* the middleware
    stack) and reaches Starlette's ServerErrorMiddleware, which unconditionally
    converts any exception into HTTP 500.  Returning JSONResponse directly is the
    correct pattern for Starlette middleware.
    """

    def __init__(self, app):
        super().__init__(app)
        self.protected_methods = {"POST", "PUT", "DELETE", "PATCH"}

        self.skip_paths = {
            "/api/v1/auth/login",
            "/api/v1/auth/register",
            "/api/v1/auth/verify-email",
            "/api/v1/auth/reset-password/request",
            "/api/v1/auth/reset-password/confirm",
            "/api/v1/auth/refresh",
        }

    # ------------------------------------------------------------------
    # Helpers — build consistent JSON error responses
    # ------------------------------------------------------------------

    @staticmethod
    def _json_403(code: str, message: str) -> JSONResponse:
        return JSONResponse(
            status_code=403,
            content={"detail": {"code": code, "message": message}},
        )

    @staticmethod
    def _json_401(code: str, message: str) -> JSONResponse:
        return JSONResponse(
            status_code=401,
            content={"detail": {"code": code, "message": message}},
        )

    @staticmethod
    def _json_500(message: str) -> JSONResponse:
        return JSONResponse(
            status_code=500,
            content={"detail": {"code": "INTERNAL_ERROR", "message": message}},
        )

    # ------------------------------------------------------------------
    # Main dispatch
    # ------------------------------------------------------------------

    async def dispatch(self, request: Request, call_next):
        if request.scope.get("type") != "http":
            return await call_next(request)

        if request.method not in self.protected_methods:
            return await call_next(request)

        if request.url.path in self.skip_paths:
            logger.debug("CSRF skip: path=%s", request.url.path)
            return await call_next(request)

        if not settings.CSRF_ENABLED:
            logger.debug("CSRF protection disabled")
            return await call_next(request)

        auth_header = request.headers.get("Authorization")

        if not auth_header or not auth_header.startswith("Bearer "):
            logger.debug(
                "CSRF skip: no auth header",
                path=request.url.path,
            )
            return await call_next(request)

        try:
            token = auth_header.replace("Bearer ", "")
            payload = decode_access_token(token)
            user_id = payload.get("sub") if payload else None

            if not user_id:
                logger.warning(
                    "CSRF check failed: invalid JWT payload",
                    path=request.url.path,
                    method=request.method,
                )
                return self._json_401("UNAUTHORIZED", "Invalid token")

            csrf_token = request.headers.get("X-CSRF-Token")

            logger.info(
                "CSRF check",
                user_id=user_id,
                path=request.url.path,
                method=request.method,
                csrf_token_present=bool(csrf_token),
                csrf_token_prefix=csrf_token[:10] if csrf_token else None,
            )

            if not csrf_token:
                logger.warning(
                    "CSRF token missing",
                    user_id=user_id,
                    path=request.url.path,
                    method=request.method,
                    client_ip=request.client.host if request.client else "unknown",
                )
                return self._json_403(
                    "CSRF_TOKEN_MISSING",
                    "CSRF token is required for this request",
                )

            # Bug fix: handle uninitialized CSRF protection (Redis unavailable at startup).
            # CSRFProtection.validate_token() already degrades gracefully when Redis is
            # temporarily unreachable (returns True).  Here we additionally guard against
            # the case where init_csrf_protection() was never called.
            try:
                csrf_protection = get_csrf_protection()
            except RuntimeError:
                logger.warning(
                    "CSRF protection not initialized (Redis unavailable at startup), "
                    "skipping token validation",
                    user_id=user_id,
                    path=request.url.path,
                )
                return await call_next(request)

            if not await csrf_protection.validate_token(user_id, csrf_token):
                logger.warning(
                    "CSRF token invalid",
                    user_id=user_id,
                    path=request.url.path,
                    method=request.method,
                    client_ip=request.client.host if request.client else "unknown",
                )
                return self._json_403(
                    "CSRF_TOKEN_INVALID",
                    "Invalid CSRF token",
                )

            logger.debug(
                "CSRF validation passed",
                user_id=user_id,
                path=request.url.path,
            )

        except Exception as e:
            logger.error(
                "CSRF validation error",
                error=str(e),
                exc_info=True,
            )
            return self._json_500("CSRF validation failed")

        return await call_next(request)
