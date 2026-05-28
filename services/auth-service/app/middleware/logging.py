import structlog
from fastapi import Request
from starlette.middleware.base import BaseHTTPMiddleware
from app.core.logging_config import get_logger


class LoggingMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request: Request, call_next):
        logger = get_logger("request")

        logger.info(
            "Incoming request",
            method=request.method,
            path=request.url.path,
            client=request.client.host if request.client else None,
        )

        try:
            response = await call_next(request)

            logger.info(
                "Request completed",
                method=request.method,
                path=request.url.path,
                status_code=response.status_code,
            )

            return response

        except Exception as e:
            logger.error(
                "Request failed",
                method=request.method,
                path=request.url.path,
                error=str(e),
                exc_info=True,
            )
            raise
