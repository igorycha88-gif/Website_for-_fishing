import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from app.core.database import Base
from app.models.password_reset_code import PasswordResetCode
from app.models.user import User
from app.crud.password_reset_code import PasswordResetCodeCRUD
from app.crud.user import UserCRUD
from app.core.security import get_password_hash
from datetime import datetime
import os

TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres_password@localhost:5433/fishing_test_db"
)

test_engine = create_async_engine(TEST_DATABASE_URL, echo=False)
TestSessionLocal = async_sessionmaker(test_engine, expire_on_commit=False, class_=AsyncSession)


@pytest.fixture(scope="function")
async def db_session():
    async with test_engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.create_all)
        except Exception:
            pass

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        try:
            await conn.run_sync(Base.metadata.drop_all)
        except Exception:
            pass


@pytest.fixture
async def test_user(db_session: AsyncSession):
    user = User(
        email="test@example.com",
        username="testuser",
        password_hash=get_password_hash("testpassword123")
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestPasswordResetCodeCRUD:
    async def test_create_code(self, db_session: AsyncSession):
        crud = PasswordResetCodeCRUD(db_session)
        code = await crud.create(
            email="test@example.com",
            code="123456",
            expire_minutes=15
        )

        assert code.id is not None
        assert code.email == "test@example.com"
        assert code.code == "123456"
        assert code.attempts == 0
        assert code.expires_at > datetime.utcnow()
        assert code.created_at is not None

    async def test_get_by_email(self, db_session: AsyncSession):
        crud = PasswordResetCodeCRUD(db_session)
        created_code = await crud.create(
            email="test@example.com",
            code="123456",
            expire_minutes=15
        )

        fetched_code = await crud.get_by_email("test@example.com")

        assert fetched_code is not None
        assert fetched_code.id == created_code.id
        assert fetched_code.code == "123456"

    async def test_get_by_email_not_found(self, db_session: AsyncSession):
        crud = PasswordResetCodeCRUD(db_session)
        code = await crud.get_by_email("nonexistent@example.com")
        assert code is None

    async def test_get_valid_code(self, db_session: AsyncSession):
        crud = PasswordResetCodeCRUD(db_session)
        await crud.create(
            email="test@example.com",
            code="123456",
            expire_minutes=15
        )

        valid_code = await crud.get_valid_code("test@example.com", "123456")

        assert valid_code is not None
        assert valid_code.code == "123456"
        assert valid_code.attempts < 3

    async def test_get_valid_code_wrong_code(self, db_session: AsyncSession):
        crud = PasswordResetCodeCRUD(db_session)
        await crud.create(
            email="test@example.com",
            code="123456",
            expire_minutes=15
        )

        invalid_code = await crud.get_valid_code("test@example.com", "000000")
        assert invalid_code is None

    async def test_get_valid_code_expired(self, db_session: AsyncSession):
        crud = PasswordResetCodeCRUD(db_session)
        await crud.create(
            email="test@example.com",
            code="123456",
            expire_minutes=-1
        )

        expired_code = await crud.get_valid_code("test@example.com", "123456")
        assert expired_code is None

    async def test_increment_attempts(self, db_session: AsyncSession):
        crud = PasswordResetCodeCRUD(db_session)
        await crud.create(
            email="test@example.com",
            code="123456",
            expire_minutes=15
        )

        await crud.increment_attempts("test@example.com")
        code = await crud.get_by_email("test@example.com")

        assert code.attempts == 1

    async def test_delete_by_email(self, db_session: AsyncSession):
        crud = PasswordResetCodeCRUD(db_session)
        await crud.create(
            email="test@example.com",
            code="123456",
            expire_minutes=15
        )

        result = await crud.delete_by_email("test@example.com")
        assert result is True

        code = await crud.get_by_email("test@example.com")
        assert code is None

    async def test_delete_by_email_not_found(self, db_session: AsyncSession):
        crud = PasswordResetCodeCRUD(db_session)
        result = await crud.delete_by_email("nonexistent@example.com")
        assert result is False

    async def test_delete_expired(self, db_session: AsyncSession):
        crud = PasswordResetCodeCRUD(db_session)
        await crud.create(
            email="test@example.com",
            code="123456",
            expire_minutes=-1
        )
        await crud.create(
            email="test2@example.com",
            code="654321",
            expire_minutes=15
        )

        deleted_count = await crud.delete_expired()
        assert deleted_count >= 1

        code1 = await crud.get_by_email("test@example.com")
        assert code1 is None

        code2 = await crud.get_by_email("test2@example.com")
        assert code2 is not None
