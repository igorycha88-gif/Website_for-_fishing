import asyncio
from app.core.database import Base, database
from app.models.user import User
from app.models.email_verification_code import EmailVerificationCode
from app.models.password_reset_code import PasswordResetCode

async def init_db():
    """Initialize database tables"""
    async with database.engine.begin() as conn:
        print("Creating database tables...")
        await conn.run_sync(Base.metadata.create_all)
        print("✓ Database tables created successfully")

if __name__ == "__main__":
    asyncio.run(init_db())
