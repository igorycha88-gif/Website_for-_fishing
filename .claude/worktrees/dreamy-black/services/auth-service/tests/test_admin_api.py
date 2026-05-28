import pytest
from fastapi.testclient import TestClient
from app.main import app
from app.crud.user import UserCRUD
from app.core.security import get_password_hash, create_access_token
from sqlalchemy.ext.asyncio import AsyncSession


@pytest.fixture
def client():
    return TestClient(app)


@pytest.fixture
def admin_user(db_session: AsyncSession):
    from app.core.database import get_db

    user_crud = UserCRUD(db_session)
    password_hash = get_password_hash("Admin@Password123!")

    admin = await user_crud.create(
        email="admin@example.com",
        username="admin",
        password_hash=password_hash,
        role="admin",
        is_verified=True,
        is_active=True
    )

    return admin


@pytest.fixture
def admin_headers(admin_user):
    token = create_access_token(data={"sub": str(admin_user.id), "role": admin_user.role})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
def regular_user(db_session: AsyncSession):
    from app.core.database import get_db

    user_crud = UserCRUD(db_session)
    password_hash = get_password_hash("User@Password123!")

    user = await user_crud.create(
        email="user@example.com",
        username="regularuser",
        password_hash=password_hash,
        role="user",
        is_verified=True,
        is_active=True
    )

    return user


@pytest.fixture
def regular_headers(regular_user):
    token = create_access_token(data={"sub": str(regular_user.id), "role": regular_user.role})
    return {"Authorization": f"Bearer {token}"}


class TestAdminCheckAccess:
    async def test_check_access_admin_user(self, client, db_session, admin_user):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.get(
            "/api/v1/admin/check-access",
            headers=admin_headers(admin_user)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_access"] is True
        assert data["user_id"] == str(admin_user.id)
        assert data["email"] == admin_user.email
        assert data["role"] == "admin"

        app.dependency_overrides.clear()

    async def test_check_access_regular_user(self, client, db_session, regular_user):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.get(
            "/api/v1/admin/check-access",
            headers=regular_headers(regular_user)
        )

        assert response.status_code == 200
        data = response.json()
        assert data["has_access"] is False
        assert data["user_id"] is None
        assert data["email"] is None
        assert data["role"] is None

        app.dependency_overrides.clear()

    async def test_check_access_no_token(self, client):
        response = client.get("/api/v1/admin/check-access")

        assert response.status_code == 401


class TestAdminDashboardStats:
    async def test_dashboard_stats_admin_user(self, client, db_session, admin_user):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.get(
            "/api/v1/admin/dashboard/stats",
            headers=admin_headers(admin_user)
        )

        assert response.status_code == 200
        data = response.json()
        assert "total_users" in data
        assert "verified_users" in data
        assert "active_users" in data
        assert "admin_count" in data
        assert "moderator_count" in data
        assert data["admin_count"] >= 1

        app.dependency_overrides.clear()

    async def test_dashboard_stats_regular_user_forbidden(self, client, db_session, regular_user):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.get(
            "/api/v1/admin/dashboard/stats",
            headers=regular_headers(regular_user)
        )

        assert response.status_code == 403
        data = response.json()
        assert "ADMIN_ACCESS_REQUIRED" in data["detail"]["code"]

        app.dependency_overrides.clear()


class TestAdminUsersList:
    async def test_users_list_admin_user(self, client, db_session, admin_user, regular_user):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.get(
            "/api/v1/admin/users",
            headers=admin_headers(admin_user)
        )

        assert response.status_code == 200
        data = response.json()
        assert "users" in data
        assert "total" in data
        assert "page" in data
        assert "page_size" in data
        assert len(data["users"]) >= 2

        app.dependency_overrides.clear()

    async def test_users_list_with_filters(self, client, db_session, admin_user):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.get(
            "/api/v1/admin/users?role=admin",
            headers=admin_headers(admin_user)
        )

        assert response.status_code == 200
        data = response.json()
        for user in data["users"]:
            assert user["role"] == "admin"

        app.dependency_overrides.clear()

    async def test_users_list_regular_user_forbidden(self, client, db_session, regular_user):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.get(
            "/api/v1/admin/users",
            headers=regular_headers(regular_user)
        )

        assert response.status_code == 403

        app.dependency_overrides.clear()

    async def test_users_list_pagination(self, client, db_session, admin_user):
        from app.core.database import get_db

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        response = client.get(
            "/api/v1/admin/users?page=1&page_size=1",
            headers=admin_headers(admin_user)
        )

        assert response.status_code == 200
        data = response.json()
        assert len(data["users"]) <= 1
        assert data["page"] == 1
        assert data["page_size"] == 1

        app.dependency_overrides.clear()


class TestRegisterWithRole:
    async def test_register_always_assigns_user_role(self, client, db_session):
        from app.core.database import get_db
        from unittest.mock import AsyncMock, patch

        def override_get_db():
            yield db_session

        app.dependency_overrides[get_db] = override_get_db

        with patch('httpx.AsyncClient.post') as mock_post:
            mock_post.return_value = AsyncMock()
            mock_post.return_value.json.return_value = {"code": "123456"}
            mock_post.return_value.status_code = 200

            response = client.post(
                "/api/v1/auth/register",
                json={
                    "email": "newuser@example.com",
                    "username": "newuser",
                    "password": "password123",
                    "role": "admin"
                }
            )

            assert response.status_code == 200

            user_crud = UserCRUD(db_session)
            user = await user_crud.get_by_email("newuser@example.com")
            assert user is not None
            assert user.role == "user"

        app.dependency_overrides.clear()
