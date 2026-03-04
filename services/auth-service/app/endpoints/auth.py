from fastapi import APIRouter, Depends, HTTPException, status, Request
from fastapi.security import HTTPBearer, HTTPAuthorizationCredentials
from fastapi_limiter.depends import RateLimiter
from sqlalchemy.ext.asyncio import AsyncSession
from sqlalchemy import select
from datetime import timedelta, datetime
import httpx
import secrets
import uuid

from app.core.security import (
    get_password_hash,
    create_access_token,
    create_refresh_token,
    decode_access_token,
)
from app.core.config import settings
from app.core.database import get_db
from app.core.logging_config import get_logger
from app.core.exceptions import EmailServiceUnavailableError
from app.core.token_blacklist import get_token_blacklist
from app.core.csrf_protection import get_csrf_protection
from app.core.error_utils import GenericErrors, add_timing_jitter
from app.schemas.auth import (
    RegisterRequest,
    VerifyEmailRequest,
    UserResponse,
    LoginRequest,
    ResetPasswordRequest,
    ResetPasswordConfirm,
    RefreshTokenRequest,
    RefreshTokenResponse,
)
from app.schemas.email import EmailVerificationResponse, MessageResponse, LogoutResponse
from app.crud.user import UserCRUD
from app.crud.refresh_token import RefreshTokenCRUD
from app.core.security import verify_password, get_password_hash
from app.crud.email_verification_code import EmailVerificationCodeCRUD
from app.crud.password_reset_token import PasswordResetTokenCRUD
from app.models.password_reset_token import PasswordResetToken

router = APIRouter()
security = HTTPBearer()
logger = get_logger(__name__)


@router.post(
    "/register",
    response_model=MessageResponse,
    dependencies=[Depends(RateLimiter(times=10, seconds=3600))]
    if settings.RATE_LIMIT_ENABLED
    else [],
)
async def register(
    request: RegisterRequest, req: Request, db: AsyncSession = Depends(get_db)
):
    logger.info("Registration attempt", email=request.email, username=request.username)
    user_crud = UserCRUD(db)

    client_ip = req.client.host if req.client else None

    existing_email = await user_crud.get_by_email(request.email)
    existing_username = await user_crud.get_by_username(request.username)

    if existing_email or existing_username:
        reason = "duplicate_email" if existing_email else "duplicate_username"
        logger.warning(
            "Registration failed - duplicate credentials",
            email=request.email,
            username=request.username,
            error_type=reason,
            ip_address=client_ip,
        )
        await add_timing_jitter()
        raise GenericErrors.registration_failed(
            email=request.email, username=request.username, ip=client_ip, reason=reason
        )

    password_hash = get_password_hash(request.password)
    user = await user_crud.create(
        email=request.email, username=request.username, password_hash=password_hash
    )
    logger.info("User created successfully", user_id=str(user.id), email=request.email)

    if settings.ENABLE_EMAIL_SENDING:
        try:
            async with httpx.AsyncClient() as client:
                api_headers = {"X-API-Key": settings.EMAIL_SERVICE_API_KEY}
                logger.info("Generating email verification code", email=request.email)
                response = await client.post(
                    f"{settings.EMAIL_SERVICE_URL}/api/v1/email/generate-code",
                    headers=api_headers,
                    timeout=10.0,
                )
                response.raise_for_status()
                code = response.json()["code"]

                logger.info(
                    "Sending verification email",
                    email=request.email,
                    username=request.username,
                )
                await client.post(
                    f"{settings.EMAIL_SERVICE_URL}/api/v1/email/send",
                    json={
                        "to_email": request.email,
                        "verification_code": code,
                        "username": request.username,
                    },
                    headers=api_headers,
                    timeout=30.0,
                )
                logger.info("Email sent successfully", email=request.email)
        except httpx.HTTPStatusError as e:
            logger.error(
                "Email service returned error",
                email=request.email,
                status_code=e.response.status_code,
                error=str(e),
                exc_info=True,
            )
            raise EmailServiceUnavailableError()
        except Exception as e:
            logger.critical(
                "Email service unavailable during registration",
                email=request.email,
                error=str(e),
                exc_info=True,
            )
            raise EmailServiceUnavailableError()
    else:
        if settings.ENVIRONMENT == "development":
            if request.email.endswith(f"@{settings.DEV_EMAIL_DOMAIN}"):
                code = secrets.token_hex(3).upper()
                logger.info(
                    "Dev mode: generated test verification code",
                    email=request.email,
                    code=code,
                )
            else:
                logger.warning(
                    "Dev mode: email not in whitelist",
                    email=request.email,
                    required_domain=settings.DEV_EMAIL_DOMAIN,
                )
                raise EmailServiceUnavailableError()
        else:
            logger.critical(
                "Email sending disabled in production mode",
                email=request.email,
            )
            raise EmailServiceUnavailableError()

    email_crud = EmailVerificationCodeCRUD(db)
    await email_crud.create(request.email, code, settings.EMAIL_CODE_EXPIRE_MINUTES)
    logger.info(
        "Verification code saved",
        email=request.email,
        code_expires_minutes=settings.EMAIL_CODE_EXPIRE_MINUTES,
    )

    return MessageResponse(
        message="Registration successful. Please check your email for verification code."
    )


@router.post(
    "/verify-email",
    response_model=EmailVerificationResponse,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
    if settings.RATE_LIMIT_ENABLED
    else [],
)
async def verify_email(
    request: VerifyEmailRequest, req: Request, db: AsyncSession = Depends(get_db)
):
    logger.info("Email verification attempt", email=request.email)
    email_crud = EmailVerificationCodeCRUD(db)
    user_crud = UserCRUD(db)

    client_ip = req.client.host if req.client else None

    verification_code = await email_crud.get_valid_code(request.email, request.code)

    if not verification_code:
        existing_code = await email_crud.get_by_email(request.email)
        await email_crud.increment_attempts(request.email)
        attempts = existing_code.attempts + 1 if existing_code else 1

        logger.warning(
            "Email verification failed - invalid code",
            email=request.email,
            ip_address=client_ip,
            attempts=attempts,
            remaining_attempts=max(0, 3 - attempts),
        )

        if attempts >= 3:
            await email_crud.delete_by_email(request.email)
            raise GenericErrors.verification_code_expired()

        raise GenericErrors.verification_failed(
            email=request.email, ip=client_ip, attempts=attempts
        )

    user = await user_crud.verify_email(request.email)
    if not user:
        logger.error("User not found during email verification", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={
                "code": "USER_NOT_FOUND",
                "message": "User not found",
            },
        )

    await email_crud.delete_by_email(request.email)

    token_version = user.token_version or 1
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}, token_version=token_version
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}, token_version=token_version
    )

    refresh_token_crud = RefreshTokenCRUD(db)
    refresh_token_payload = decode_access_token(refresh_token)
    jti = (
        refresh_token_payload.get("jti") if refresh_token_payload else str(uuid.uuid4())
    )

    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await refresh_token_crud.create(
        user_id=str(user.id), token=refresh_token, jti=jti, expires_at=expires_at
    )

    logger.info(
        "Email verified successfully", user_id=str(user.id), email=request.email
    )

    try:
        csrf_protection = get_csrf_protection()
        csrf_token = await csrf_protection.generate_token(str(user.id))
    except Exception as e:
        logger.warning("Failed to generate CSRF token", error=str(e))
        csrf_token = None

    return EmailVerificationResponse(
        success=True,
        message="Email verified successfully",
        access_token=access_token,
        refresh_token=refresh_token,
        csrf_token=csrf_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.post(
    "/login",
    response_model=EmailVerificationResponse,
    dependencies=[Depends(RateLimiter(times=5, seconds=60))]
    if settings.RATE_LIMIT_ENABLED
    else [],
)
async def login(request: LoginRequest, db: AsyncSession = Depends(get_db)):
    logger.info("Login attempt", email=request.email)
    user_crud = UserCRUD(db)

    user = await user_crud.get_by_email(request.email)
    if not user:
        logger.warning("Login failed - user not found", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password",
            },
        )

    if not verify_password(request.password, str(user.password_hash)):
        logger.warning("Login failed - invalid password", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_CREDENTIALS",
                "message": "Invalid email or password",
            },
        )

    if not bool(user.is_verified):
        logger.warning("Login failed - email not verified", email=request.email)
        raise HTTPException(
            status_code=status.HTTP_403_FORBIDDEN,
            detail={
                "code": "EMAIL_NOT_VERIFIED",
                "message": "Please verify your email first",
            },
        )

    token_version = user.token_version or 1
    access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role}, token_version=token_version
    )
    refresh_token = create_refresh_token(
        data={"sub": str(user.id)}, token_version=token_version
    )

    refresh_token_crud = RefreshTokenCRUD(db)
    refresh_token_payload = decode_access_token(refresh_token)
    jti = (
        refresh_token_payload.get("jti") if refresh_token_payload else str(uuid.uuid4())
    )

    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await refresh_token_crud.create(
        user_id=str(user.id), token=refresh_token, jti=jti, expires_at=expires_at
    )

    logger.info("Login successful", user_id=str(user.id), email=request.email)

    try:
        csrf_protection = get_csrf_protection()
        csrf_token = await csrf_protection.generate_token(str(user.id))
        logger.info(
            "CSRF token generated for login",
            user_id=str(user.id),
            csrf_token_prefix=csrf_token[:10] if csrf_token else None,
        )
    except Exception as e:
        logger.warning("Failed to generate CSRF token", error=str(e))
        csrf_token = None

    response = EmailVerificationResponse(
        success=True,
        message="Login successful",
        access_token=access_token,
        refresh_token=refresh_token,
        csrf_token=csrf_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )
    logger.info("Login response prepared", has_csrf_token=bool(csrf_token))
    return response


@router.post("/logout", response_model=LogoutResponse)
async def logout(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    logger.info("Logout attempt")

    token = credentials.credentials
    payload = decode_access_token(token)

    if not payload:
        logger.warning("Logout failed - invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Authentication required"},
        )

    jti = payload.get("jti")
    token_type = payload.get("type")

    if not jti:
        logger.warning("Logout failed - no jti in token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Invalid token format"},
        )

    try:
        blacklist = await get_token_blacklist()
        expires_in_seconds = settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60
        await blacklist.add_access_token(jti, expires_in_seconds)
        logger.info("Access token blacklisted", jti=jti)
    except Exception as e:
        logger.warning("Redis unavailable during logout", error=str(e))

    user_id = payload.get("sub")
    if user_id:
        try:
            csrf_protection = get_csrf_protection()
            await csrf_protection.invalidate_token(user_id)
            logger.info("CSRF token invalidated", user_id=user_id)
        except Exception as e:
            logger.warning("Failed to invalidate CSRF token", error=str(e))

    if token_type == "refresh":
        if user_id:
            refresh_token_crud = RefreshTokenCRUD(db)
            await refresh_token_crud.revoke(jti)
            logger.info("Refresh token revoked in database", jti=jti, user_id=user_id)

    logger.info("Logout successful")
    return LogoutResponse()


@router.post("/refresh", response_model=RefreshTokenResponse)
async def refresh_token(
    request: RefreshTokenRequest,
    db: AsyncSession = Depends(get_db),
):
    logger.info("Token refresh attempt")

    payload = decode_access_token(request.refresh_token)

    if not payload:
        logger.warning("Token refresh failed - invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "REFRESH_TOKEN_EXPIRED",
                "message": "Refresh token has expired",
            },
        )

    token_type = payload.get("type")
    if token_type != "refresh":
        logger.warning("Token refresh failed - wrong token type", type=token_type)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN_TYPE",
                "message": "Token is not a refresh token",
            },
        )

    jti = payload.get("jti")
    user_id = payload.get("sub")
    token_version = payload.get("ver", 1)

    if not jti or not user_id:
        logger.warning("Token refresh failed - missing jti or sub")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "INVALID_TOKEN", "message": "Invalid token format"},
        )

    try:
        blacklist = await get_token_blacklist()
        if await blacklist.is_refresh_token_revoked(jti):
            logger.warning("Token refresh failed - token revoked in blacklist", jti=jti)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={
                    "code": "REFRESH_TOKEN_REVOKED",
                    "message": "Refresh token has been revoked",
                },
            )
    except Exception as e:
        logger.warning("Redis unavailable during token refresh check", error=str(e))

    refresh_token_crud = RefreshTokenCRUD(db)

    if await refresh_token_crud.is_revoked(jti):
        logger.warning("Token refresh failed - token revoked in database", jti=jti)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "REFRESH_TOKEN_REVOKED",
                "message": "Refresh token has been revoked",
            },
        )

    user_crud = UserCRUD(db)
    user = await user_crud.get_by_id(user_id)

    if not user:
        logger.warning("Token refresh failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    current_token_version = user.token_version or 1
    if token_version != current_token_version:
        logger.warning(
            "Token refresh failed - token version mismatch",
            token_version=token_version,
            current_version=current_token_version,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_REVOKED", "message": "Token has been invalidated"},
        )

    new_access_token = create_access_token(
        data={"sub": str(user.id), "role": user.role},
        token_version=current_token_version,
    )
    new_refresh_token = create_refresh_token(
        data={"sub": str(user.id)}, token_version=current_token_version
    )

    new_payload = decode_access_token(new_refresh_token)
    new_jti = new_payload.get("jti") if new_payload else str(uuid.uuid4())

    await refresh_token_crud.revoke(jti, replaced_by=new_jti)

    try:
        blacklist = await get_token_blacklist()
        refresh_expires_seconds = settings.REFRESH_TOKEN_EXPIRE_DAYS * 86400
        await blacklist.add_refresh_token(jti, refresh_expires_seconds)
        logger.info("Old refresh token blacklisted", old_jti=jti)
    except Exception as e:
        logger.warning("Redis unavailable during old token blacklist", error=str(e))

    expires_at = datetime.utcnow() + timedelta(days=settings.REFRESH_TOKEN_EXPIRE_DAYS)
    await refresh_token_crud.create(
        user_id=str(user.id),
        token=new_refresh_token,
        jti=new_jti,
        expires_at=expires_at,
    )

    logger.info("Token refresh successful", user_id=str(user.id))

    try:
        csrf_protection = get_csrf_protection()
        csrf_token = await csrf_protection.refresh_token(str(user.id))
    except Exception as e:
        logger.warning("Failed to generate CSRF token", error=str(e))
        csrf_token = None

    return RefreshTokenResponse(
        access_token=new_access_token,
        refresh_token=new_refresh_token,
        csrf_token=csrf_token,
        expires_in=settings.ACCESS_TOKEN_EXPIRE_MINUTES * 60,
    )


@router.get("/users/me", response_model=UserResponse)
async def get_current_user(
    credentials: HTTPAuthorizationCredentials = Depends(security),
    db: AsyncSession = Depends(get_db),
):
    logger.debug("Get current user request")
    token = credentials.credentials
    payload = decode_access_token(token)
    if not payload:
        logger.warning("Get current user failed - invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token"},
        )

    user_id = payload.get("sub")
    jti = payload.get("jti")
    token_version = payload.get("ver")
    token_type = payload.get("type")

    if not user_id:
        logger.warning("Get current user failed - invalid token payload")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "UNAUTHORIZED", "message": "Invalid token"},
        )

    if token_type != "access":
        logger.warning("Get current user failed - wrong token type")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={
                "code": "INVALID_TOKEN_TYPE",
                "message": "Token is not an access token",
            },
        )

    try:
        blacklist = await get_token_blacklist()
        if jti and await blacklist.is_access_token_revoked(jti):
            logger.warning("Get current user failed - token revoked", jti=jti)
            raise HTTPException(
                status_code=status.HTTP_401_UNAUTHORIZED,
                detail={"code": "TOKEN_REVOKED", "message": "Token has been revoked"},
            )
    except Exception as e:
        logger.warning("Redis unavailable during token validation", error=str(e))

    user_crud = UserCRUD(db)
    user = await user_crud.get_by_id(user_id)

    if not user:
        logger.warning("Get current user failed - user not found", user_id=user_id)
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail={"code": "USER_NOT_FOUND", "message": "User not found"},
        )

    current_token_version = user.token_version or 1
    if token_version and token_version != current_token_version:
        logger.warning(
            "Get current user failed - token version mismatch",
            token_version=token_version,
            current_version=current_token_version,
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail={"code": "TOKEN_REVOKED", "message": "Token has been invalidated"},
        )

    logger.info("Get current user successful", user_id=user_id)
    return UserResponse.model_validate(user)


@router.post(
    "/reset-password/request",
    response_model=MessageResponse,
    dependencies=[Depends(RateLimiter(times=3, seconds=3600))]
    if settings.RATE_LIMIT_ENABLED
    else [],
)
async def request_password_reset(
    request_body: ResetPasswordRequest, req: Request, db: AsyncSession = Depends(get_db)
):
    logger.info("Password reset request", email=request_body.email)
    user_crud = UserCRUD(db)
    password_reset_token_crud = PasswordResetTokenCRUD(db)

    user = await user_crud.get_by_email(request_body.email)
    if not user:
        logger.warning(
            "Password reset failed - email not found", email=request_body.email
        )
        return MessageResponse(
            message="Если этот email зарегистрирован, инструкция по сбросу пароля будет отправлена"
        )

    reset_token = secrets.token_urlsafe(48)
    token_hash = get_password_hash(reset_token)

    client_ip = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent", None)

    await password_reset_token_crud.invalidate_user_tokens(str(user.id))

    expires_at = datetime.utcnow() + timedelta(hours=1)
    await password_reset_token_crud.create(
        user_id=str(user.id),
        token_hash=token_hash,
        expires_at=expires_at,
        ip_address=client_ip,
        user_agent=user_agent,
    )

    logger.info(
        "Password reset token generated", user_id=str(user.id), email=request_body.email
    )

    if settings.ENABLE_EMAIL_SENDING:
        try:
            async with httpx.AsyncClient() as client:
                api_headers = {"X-API-Key": settings.EMAIL_SERVICE_API_KEY}
                reset_link = (
                    f"{settings.FRONTEND_URL}/reset-password?token={reset_token}"
                )

                await client.post(
                    f"{settings.EMAIL_SERVICE_URL}/api/v1/email/send",
                    json={
                        "to_email": user.email,
                        "verification_code": reset_link,
                        "username": user.username,
                    },
                    headers=api_headers,
                    timeout=30.0,
                )
                logger.info("Password reset email sent", email=user.email)
        except Exception as e:
            logger.error(
                "Failed to send password reset email",
                email=user.email,
                error=str(e),
                exc_info=True,
            )

    return MessageResponse(
        message="Если этот email зарегистрирован, инструкция по сбросу пароля будет отправлена"
    )


@router.post("/reset-password/confirm", response_model=MessageResponse)
async def confirm_password_reset(
    request_body: ResetPasswordConfirm, req: Request, db: AsyncSession = Depends(get_db)
):
    logger.info("Password reset confirmation attempt")

    if len(request_body.token) != 64:
        logger.warning("Password reset failed - invalid token length")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    password_reset_token_crud = PasswordResetTokenCRUD(db)

    stored_tokens = await db.execute(
        select(PasswordResetToken).where(PasswordResetToken.used == False)
    )
    stored_tokens = stored_tokens.scalars().all()

    matching_token = None
    for stored_token in stored_tokens:
        if verify_password(request_body.token, stored_token.token_hash):
            matching_token = stored_token
            break

    if not matching_token:
        logger.warning("Password reset failed - invalid token")
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    if matching_token.expires_at < datetime.utcnow():
        logger.warning(
            "Password reset failed - token expired", token_id=str(matching_token.id)
        )
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED, detail="Invalid or expired token"
        )

    user_crud = UserCRUD(db)
    user = await user_crud.get_by_id(str(matching_token.user_id))

    if not user:
        logger.warning(
            "Password reset failed - user not found",
            user_id=str(matching_token.user_id),
        )
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND, detail="User not found"
        )

    client_ip = req.client.host if req.client else None
    user_agent = req.headers.get("user-agent", None)

    await password_reset_token_crud.mark_as_used(
        token_id=matching_token.id, ip_address=client_ip, user_agent=user_agent
    )

    password_hash = get_password_hash(request_body.new_password)
    await user_crud.update_password(str(user.id), password_hash)

    await user_crud.increment_token_version(str(user.id))
    logger.info(
        "Password reset successful, token version incremented", user_id=str(user.id)
    )

    try:
        csrf_protection = get_csrf_protection()
        await csrf_protection.invalidate_token(str(user.id))
        logger.info("CSRF token invalidated after password reset", user_id=str(user.id))
    except Exception as e:
        logger.warning("Failed to invalidate CSRF token", error=str(e))

    if settings.ENABLE_EMAIL_SENDING:
        try:
            async with httpx.AsyncClient() as client:
                api_headers = {"X-API-Key": settings.EMAIL_SERVICE_API_KEY}

                await client.post(
                    f"{settings.EMAIL_SERVICE_URL}/api/v1/email/send",
                    json={
                        "to_email": user.email,
                        "verification_code": f"Password changed at {datetime.utcnow().isoformat()} from IP: {client_ip}",
                        "username": user.username,
                    },
                    headers=api_headers,
                    timeout=30.0,
                )
                logger.info("Password changed notification sent", email=user.email)
        except Exception as e:
            logger.error(
                "Failed to send password changed notification",
                email=user.email,
                error=str(e),
                exc_info=True,
            )

    return MessageResponse(message="Пароль успешно изменен")
