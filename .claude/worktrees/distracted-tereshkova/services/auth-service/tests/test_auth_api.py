import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.crud.user import UserCRUD
from app.crud.email_verification_code import EmailVerificationCodeCRUD
from app.core.security import get_password_hash, create_access_token
from unittest.mock import AsyncMock, patch


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def mock_email_service():
    with patch('httpx.AsyncClient.post') as mock_post:
        mock_post.return_value = AsyncMock()
        mock_post.return_value.json.return_value = {"code": "123456"}
        mock_post.return_value.status_code = 200
        yield mock_post


@pytest.fixture
def auth_headers(test_user):
    token = create_access_token(data={"sub": str(test_user.id)})
    return {"Authorization": f"Bearer {token}"}


class TestRegisterAPI:
    async def test_register_success(self, client, db_session, mock_email_service):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "newuser@example.com",
                "username": "newuser",
                "password": "password123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert "message" in data
        assert "verification code" in data["message"].lower()

        user_crud = UserCRUD(db_session)
        user = await user_crud.get_by_email("newuser@example.com")
        assert user is not None
        assert user.username == "newuser"

        email_crud = EmailVerificationCodeCRUD(db_session)
        code = await email_crud.get_by_email("newuser@example.com")
        assert code is not None

        app.dependency_overrides.clear()

    async def test_register_email_exists(self, client, db_session, test_user, mock_email_service):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": test_user.email,
                "username": "differentuser",
                "password": "password123"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "EMAIL_ALREADY_EXISTS" in data["detail"]["code"]

        app.dependency_overrides.clear()

    async def test_register_username_exists(self, client, db_session, test_user, mock_email_service):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.post(
            "/api/v1/auth/register",
            json={
                "email": "different@example.com",
                "username": test_user.username,
                "password": "password123"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "USERNAME_ALREADY_EXISTS" in data["detail"]["code"]

        app.dependency_overrides.clear()


class TestVerifyEmailAPI:
    async def test_verify_email_success(self, client, db_session, test_user, mock_email_service):
        from app.core.database import get_db
        from app.crud.email_verification_code import EmailVerificationCodeCRUD

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        email_crud = EmailVerificationCodeCRUD(db_session)
        await email_crud.create(
            email=test_user.email,
            code="123456",
            expire_minutes=15
        )

        response = client.post(
            "/api/v1/auth/verify-email",
            json={
                "email": test_user.email,
                "code": "123456"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data

        app.dependency_overrides.clear()

    async def test_verify_email_invalid_code(self, client, db_session, test_user, mock_email_service):
        from app.core.database import get_db
        from app.crud.email_verification_code import EmailVerificationCodeCRUD

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        email_crud = EmailVerificationCodeCRUD(db_session)
        await email_crud.create(
            email=test_user.email,
            code="123456",
            expire_minutes=15
        )

        response = client.post(
            "/api/v1/auth/verify-email",
            json={
                "email": test_user.email,
                "code": "000000"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "INVALID_OR_EXPIRED_CODE" in data["detail"]["code"]
        assert "remaining_attempts" in data["detail"]["details"]

        app.dependency_overrides.clear()


class TestPasswordResetAPI:
    async def test_reset_password_request_success(self, client, db_session, test_user, mock_email_service):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.post(
            "/api/v1/auth/reset-password/request",
            json={"email": test_user.email}
        )

        assert response.status_code == 200
        data = response.json()
        assert "Password reset code sent" in data["message"]

        app.dependency_overrides.clear()

    async def test_reset_password_request_user_not_found(self, client, db_session, mock_email_service):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.post(
            "/api/v1/auth/reset-password/request",
            json={"email": "nonexistent@example.com"}
        )

        assert response.status_code == 404
        data = response.json()
        assert "USER_NOT_FOUND" in data["detail"]["code"]

        app.dependency_overrides.clear()

    async def test_reset_password_confirm_success(self, client, db_session, test_user, mock_email_service):
        from app.core.database import get_db
        from app.crud.password_reset_code import PasswordResetCodeCRUD

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        reset_crud = PasswordResetCodeCRUD(db_session)
        await reset_crud.create(
            email=test_user.email,
            code="123456",
            expire_minutes=15
        )

        response = client.post(
            "/api/v1/auth/reset-password/confirm",
            json={
                "email": test_user.email,
                "code": "123456",
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == 200
        data = response.json()
        assert data["success"] is True
        assert "access_token" in data

        app.dependency_overrides.clear()

    async def test_reset_password_confirm_invalid_code(self, client, db_session, test_user, mock_email_service):
        from app.core.database import get_db
        from app.crud.password_reset_code import PasswordResetCodeCRUD

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        reset_crud = PasswordResetCodeCRUD(db_session)
        await reset_crud.create(
            email=test_user.email,
            code="123456",
            expire_minutes=15
        )

        response = client.post(
            "/api/v1/auth/reset-password/confirm",
            json={
                "email": test_user.email,
                "code": "000000",
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "INVALID_OR_EXPIRED_CODE" in data["detail"]["code"]

        app.dependency_overrides.clear()

    async def test_reset_password_confirm_max_attempts(self, client, db_session, test_user, mock_email_service):
        from app.core.database import get_db
        from app.crud.password_reset_code import PasswordResetCodeCRUD

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        reset_crud = PasswordResetCodeCRUD(db_session)
        await reset_crud.create(
            email=test_user.email,
            code="123456",
            expire_minutes=15
        )
        code = await reset_crud.get_by_email(test_user.email)
        await db_session.execute(
            f"UPDATE password_reset_codes SET attempts = 3 WHERE id = '{code.id}'"
        )
        await db_session.commit()

        response = client.post(
            "/api/v1/auth/reset-password/confirm",
            json={
                "email": test_user.email,
                "code": "123456",
                "new_password": "newpassword123"
            }
        )

        assert response.status_code == 400
        data = response.json()
        assert "INVALID_OR_EXPIRED_CODE" in data["detail"]["code"]

        app.dependency_overrides.clear()
