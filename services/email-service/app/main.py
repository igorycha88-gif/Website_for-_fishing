from fastapi import FastAPI
from app.core.config import settings
from app.core.logging_config import configure_logging
from app.middleware.logging import LoggingMiddleware
from app.api.v1.router import router

configure_logging()

app = FastAPI(
    title="Email Service",
    description="Email service for sending verification emails",
    version="1.0.0",
)

app.add_middleware(LoggingMiddleware)
app.include_router(router, prefix="/api/v1/email")


@app.get("/health")
async def health_check():
    return {
        "status": "healthy",
        "service": "email-service",
        "version": "1.0.0",
        "email_enabled": settings.ENABLE_EMAIL_SENDING,
    }


@app.get("/")
async def root():
    return {"message": "Email Service is running"}
