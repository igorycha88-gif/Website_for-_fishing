import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from fastapi.testclient import TestClient
from app.main import app
from app.core.database import Base
from app.crud.user import UserCRUD
from app.crud.email_verification_code import EmailVerificationCodeCRUD
from app.core.security import get_password_hash
from app.models.password_reset_code import PasswordResetCode
from app.models.email_verification_code import EmailVerificationCode
from app.models.user import User
from unittest.mock import AsyncMock, patch
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
        await conn.run_sync(Base.metadata.drop_all)
        await conn.run_sync(Base.metadata.create_all)

    async with TestSessionLocal() as session:
        yield session

    async with test_engine.begin() as conn:
        await conn.run_sync(Base.metadata.drop_all)


@pytest.fixture
def client():
    return TestClient(app)


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


@pytest.fixture
async def unverified_user(db_session: AsyncSession):
    user = User(
        email="unverified@example.com",
        username="unverifieduser",
        password_hash=get_password_hash("testpassword123"),
        is_verified=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def verified_user(db_session: AsyncSession):
    user = User(
        email="verified@example.com",
        username="verifieduser",
        password_hash=get_password_hash("testpassword123"),
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def mock_email_service():
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value = AsyncMock()
        mock_post.return_value.json.return_value = {"code": "654321"}
        mock_post.return_value.status_code = 200
        yield mock_post


@pytest.fixture
async def unverified_user(db_session):
    user = User(
        email="unverified@example.com",
        username="unverifieduser",
        password_hash=get_password_hash("testpassword123"),
        is_verified=False
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
async def verified_user(db_session):
    user = User(
        email="verified@example.com",
        username="verifieduser",
        password_hash=get_password_hash("testpassword123"),
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


class TestResendVerificationAPI:
    @pytest.mark.asyncio
    async def test_resend_verification_success(self, client, db_session, unverified_user, mock_email_service):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.post(
            "/api/v1/auth/resend-verification",
            json={"email": unverified_user.email}
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "sent to your email" in data["message"].lower()

        email_crud = EmailVerificationCodeCRUD(db_session)
        code = await email_crud.get_by_email(unverified_user.email)
        assert code is not None
        assert code.code == "654321"

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_resend_verification_user_not_found(self, client, db_session, mock_email_service):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.post(
            "/api/v1/auth/resend-verification",
            json={"email": "nonexistent@example.com"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "USER_NOT_FOUND" in data["detail"]["code"]

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_resend_verification_already_verified(self, client, db_session, verified_user, mock_email_service):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.post(
            "/api/v1/auth/resend-verification",
            json={"email": verified_user.email}
        )

        assert response.status_code == 400
        data = response.json()
        assert "EMAIL_ALREADY_VERIFIED" in data["detail"]["code"]

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_resend_verification_deletes_old_code(self, client, db_session, unverified_user, mock_email_service):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        email_crud = EmailVerificationCodeCRUD(db_session)
        await email_crud.create(
            email=unverified_user.email,
            code="123456",
            expire_minutes=15
        )

        old_code = await email_crud.get_by_email(unverified_user.email)
        assert old_code is not None
        assert old_code.code == "123456"

        response = client.post(
            "/api/v1/auth/resend-verification",
            json={"email": unverified_user.email}
        )

        assert response.status_code == 200

        new_code = await email_crud.get_by_email(unverified_user.email)
        assert new_code is not None
        assert new_code.code == "654321"
        assert old_code.code != new_code.code

        app.dependency_overrides.clear()

    @pytest.mark.asyncio
    async def test_resend_verification_email_service_error(self, client, db_session, unverified_user):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.side_effect = Exception("Email service error")

            response = client.post(
                "/api/v1/auth/resend-verification",
                json={"email": unverified_user.email}
            )

            assert response.status_code == 500
            data = response.json()
            assert "EMAIL_SEND_FAILED" in data["detail"]["code"]

        app.dependency_overrides.clear()
