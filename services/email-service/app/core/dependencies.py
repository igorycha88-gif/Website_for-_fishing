from fastapi import Request, HTTPException
from app.core.config import settings
from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def verify_api_key(request: Request) -> str:
    api_key = request.headers.get("X-API-Key")

    if not api_key:
        logger.warning(
            "API key missing in request",
            path=request.url.path,
            method=request.method,
        )
        raise HTTPException(
            status_code=401,
            detail={
                "code": "API_KEY_REQUIRED",
                "message": "X-API-Key header is required"
            }
        )

    if api_key != settings.EMAIL_SERVICE_API_KEY:
        logger.warning(
            "Invalid API key attempt",
            path=request.url.path,
            method=request.method,
        )
        raise HTTPException(
            status_code=403,
            detail={
                "code": "INVALID_API_KEY",
                "message": "Invalid API key"
            }
        )

    return api_key
