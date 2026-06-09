from contextlib import asynccontextmanager
from fastapi import FastAPI, Request, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.status import HTTP_429_TOO_MANY_REQUESTS
from sqlalchemy import text
from app.api.v1 import router as v1_router
from app.core.config import settings
from app.core.logging_config import configure_logging, get_logger
from app.core.rate_limiter import init_rate_limiter
from app.core.database import redis_client, database
from app.core.csrf_protection import init_csrf_protection
from app.middleware.logging import LoggingMiddleware
from app.middleware.csrf import CSRFMiddleware

configure_logging()
logger = get_logger(__name__)


async def apply_pending_migrations() -> None:
    """
    Apply pending DB migrations at service startup.

    Uses IF NOT EXISTS — safe to run on every startup.
    Prevents startup failures when the model has new columns
    that were not yet applied to the database.
    """
    migrations = [
        # Migration 006: birth_date and bio fields for user profile
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_date DATE",
        "ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT",
    ]
    try:
        async with database.engine.begin() as conn:
            for sql in migrations:
                await conn.execute(text(sql))
        logger.info(
            "DB startup migration check completed",
            service="auth-service",
            migrations_count=len(migrations),
        )
    except Exception as e:
        logger.error(
            "DB startup migration check failed",
            service="auth-service",
            error=str(e),
            exc_info=True,
        )


@asynccontextmanager
async def lifespan(app: FastAPI):
    # Apply pending migrations before anything else so that model ↔ DB schema
    # is always in sync even if `docker-compose up` happens before the DBA
    # manually runs migration scripts.
    await apply_pending_migrations()

    if settings.RATE_LIMIT_ENABLED:
        try:
            await init_rate_limiter(app)
        except Exception as e:
            logger.warning(f"Rate limiter initialization failed, continuing without rate limiting: {e}")

    if settings.CSRF_ENABLED:
        try:
            await init_csrf_protection(redis_client)
            logger.info("CSRF protection initialized")
        except Exception as e:
            logger.warning(f"CSRF protection initialization failed: {e}")

    yield


app = FastAPI(
    title="Auth Service",
    description="Authentication and authorization service",
    version="1.0.0",
    lifespan=lifespan,
)


@app.exception_handler(HTTPException)
async def http_exception_handler(request: Request, exc: HTTPException):
    if exc.status_code == HTTP_429_TOO_MANY_REQUESTS:
        logger.warning(
            "Rate limit exceeded",
            client_ip=request.client.host if request.client else "unknown",
            path=request.url.path,
        )
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
    
    if isinstance(exc.detail, dict):
        return JSONResponse(
            status_code=exc.status_code,
            content={"detail": exc.detail}
        )
    
    return JSONResponse(
        status_code=exc.status_code,
        content={"detail": {"code": "HTTP_ERROR", "message": str(exc.detail)}}
    )

app.add_middleware(CSRFMiddleware)
app.add_middleware(LoggingMiddleware)
app.add_middleware(
    CORSMiddleware,
    allow_origins=settings.cors_origins_list,
    allow_credentials=True,
    allow_methods=["GET", "POST", "PUT", "DELETE", "OPTIONS"],
    allow_headers=["Content-Type", "Authorization", "X-Requested-With", "X-CSRF-Token"],
)

app.include_router(v1_router, prefix="/api/v1")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "auth-service",
        "version": "1.0.0",
        "email_enabled": settings.ENABLE_EMAIL_SENDING,
    }
