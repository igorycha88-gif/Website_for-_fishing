import asyncio
import random
from typing import Any, Dict, Optional

from fastapi import HTTPException, status

from app.core.logging_config import get_logger

logger = get_logger(__name__)


async def add_timing_jitter(min_ms: int = 50, max_ms: int = 150) -> None:
    delay_ms = random.randint(min_ms, max_ms)
    await asyncio.sleep(delay_ms / 1000.0)


def create_generic_error(
    error_code: str,
    message: str,
    log_details: Optional[Dict[str, Any]] = None,
    status_code: int = status.HTTP_400_BAD_REQUEST,
) -> HTTPException:
    if log_details:
        logger.warning(f"Error: {error_code}", **log_details)

    return HTTPException(
        status_code=status_code,
        detail={"code": error_code, "message": message},
    )


class GenericErrors:
    @staticmethod
    def registration_failed(
        email: str, username: str, ip: Optional[str], reason: str
    ) -> HTTPException:
        return create_generic_error(
            error_code="REGISTRATION_FAILED",
            message="Unable to complete registration. Please try with different credentials.",
            log_details={
                "email": email,
                "username": username,
                "ip_address": ip,
                "reason": reason,
            },
        )

    @staticmethod
    def verification_failed(
        email: str, ip: Optional[str], attempts: int
    ) -> HTTPException:
        return create_generic_error(
            error_code="INVALID_CODE",
            message="Invalid verification code",
            log_details={
                "email": email,
                "ip_address": ip,
                "attempts": attempts,
                "remaining_attempts": max(0, 3 - attempts),
            },
        )

    @staticmethod
    def verification_code_expired() -> HTTPException:
        return HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail={
                "code": "VERIFICATION_CODE_EXPIRED",
                "message": "Too many attempts. Please request a new verification code.",
            },
        )
