import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.core.database import Base
from app.models.password_reset_code import PasswordResetCode
from app.models.email_verification_code import EmailVerificationCode
from app.models.user import User
import os

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres_password@localhost:5432/fishing_test_db"
)

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture
async def db_session():
    async with test_engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except Exception as e:
            pass

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except Exception as e:
            pass


@pytest.fixture
async def test_user(db_session: AsyncSession):
    from app.core.security import get_password_hash
    
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash=get_password_hash("testpassword123")
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user
