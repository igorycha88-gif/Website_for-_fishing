"""
Tests for user profile update functionality.
Covers Bug Fix:
  - birth_date and bio fields missing from UserUpdate / UserResponse schemas
  - Empty string to None conversion for text fields
  - CSRF middleware graceful degradation when _csrf_protection not initialized
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from datetime import date, datetime
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.schemas.auth import UserUpdate, UserResponse
from app.middleware.csrf import CSRFMiddleware


# ============================================================
# UserUpdate schema tests
# ============================================================

class TestUserUpdateSchema:
    def test_valid_full_profile_update(self):
        """All profile fields (including birth_date and bio) are accepted."""
        data = UserUpdate(
            first_name="Иван",
            last_name="Петров",
            phone="+79991234567",
            birth_date=date(1990, 5, 15),
            city="Москва",
            bio="Рыбак со стажем 10 лет",
        )
        assert data.first_name == "Иван"
        assert data.last_name == "Петров"
        assert data.birth_date == date(1990, 5, 15)
        assert data.bio == "Рыбак со стажем 10 лет"
        assert data.city == "Москва"

    def test_empty_string_first_name_converted_to_none(self):
        """Empty first_name string must be converted to None (not cause 422)."""
        data = UserUpdate(first_name="")
        assert data.first_name is None

    def test_empty_string_last_name_converted_to_none(self):
        data = UserUpdate(last_name="")
        assert data.last_name is None

    def test_empty_string_phone_converted_to_none(self):
        data = UserUpdate(phone="")
        assert data.phone is None

    def test_empty_string_city_converted_to_none(self):
        """Empty city must become None — previously failed the regex pattern."""
        data = UserUpdate(city="")
        assert data.city is None

    def test_whitespace_only_city_converted_to_none(self):
        """Whitespace-only city must also become None."""
        data = UserUpdate(city="   ")
        assert data.city is None

    def test_empty_string_bio_converted_to_none(self):
        data = UserUpdate(bio="")
        assert data.bio is None

    def test_none_birth_date_accepted(self):
        data = UserUpdate(birth_date=None)
        assert data.birth_date is None

    def test_birth_date_from_isoformat_string(self):
        """Frontend sends birth_date as ISO date string."""
        data = UserUpdate.model_validate({"birth_date": "1990-05-15"})
        assert data.birth_date == date(1990, 5, 15)

    def test_bio_max_length(self):
        """bio field should allow up to 2000 characters."""
        long_bio = "А" * 2000
        data = UserUpdate(bio=long_bio)
        assert data.bio == long_bio

    def test_bio_exceeding_max_length_raises(self):
        """bio longer than 2000 characters should raise ValidationError."""
        from pydantic import ValidationError
        with pytest.raises(ValidationError):
            UserUpdate(bio="А" * 2001)

    def test_all_fields_none_is_valid(self):
        """Sending all-None update is valid (no-op update)."""
        data = UserUpdate()
        assert data.first_name is None
        assert data.last_name is None
        assert data.birth_date is None
        assert data.bio is None
        assert data.city is None

    def test_exclude_unset_only_includes_provided_fields(self):
        """model_dump(exclude_unset=True) should only include explicitly provided fields."""
        data = UserUpdate(first_name="Иван", city="Москва")
        dumped = data.model_dump(exclude_unset=True)
        assert "first_name" in dumped
        assert "city" in dumped
        # Fields not passed should NOT appear (they weren't "set")
        assert "birth_date" not in dumped
        assert "bio" not in dumped
        assert "last_name" not in dumped

    def test_birth_date_and_bio_included_when_provided(self):
        """When birth_date and bio are provided, they appear in model_dump."""
        data = UserUpdate(birth_date=date(1985, 3, 20), bio="Люблю рыбачить")
        dumped = data.model_dump(exclude_unset=True)
        assert "birth_date" in dumped
        assert "bio" in dumped
        assert dumped["birth_date"] == date(1985, 3, 20)
        assert dumped["bio"] == "Люблю рыбачить"


# ============================================================
# UserResponse schema tests
# ============================================================

class TestUserResponseSchema:
    def _base_user_data(self) -> dict:
        return {
            "id": "550e8400-e29b-41d4-a716-446655440000",
            "email": "test@example.com",
            "username": "testuser",
            "is_verified": True,
            "created_at": datetime(2024, 1, 1, 12, 0, 0),
        }

    def test_response_contains_birth_date_field(self):
        """UserResponse must include birth_date field."""
        data = UserResponse(**self._base_user_data(), birth_date=date(1990, 5, 15))
        assert data.birth_date == date(1990, 5, 15)

    def test_response_contains_bio_field(self):
        """UserResponse must include bio field."""
        data = UserResponse(**self._base_user_data(), bio="Рыбак")
        assert data.bio == "Рыбак"

    def test_response_birth_date_defaults_to_none(self):
        """birth_date should default to None if not provided."""
        data = UserResponse(**self._base_user_data())
        assert data.birth_date is None

    def test_response_bio_defaults_to_none(self):
        """bio should default to None if not provided."""
        data = UserResponse(**self._base_user_data())
        assert data.bio is None

    def test_uuid_id_is_converted_to_string(self):
        """UUID id must be converted to str by the validator."""
        import uuid
        user_data = self._base_user_data()
        user_data["id"] = uuid.UUID("550e8400-e29b-41d4-a716-446655440000")
        data = UserResponse(**user_data)
        assert isinstance(data.id, str)
        assert data.id == "550e8400-e29b-41d4-a716-446655440000"

    def test_response_from_orm_with_new_fields(self):
        """model_validate should pick up birth_date and bio from ORM object."""
        mock_user = MagicMock()
        mock_user.id = "550e8400-e29b-41d4-a716-446655440000"
        mock_user.email = "test@example.com"
        mock_user.username = "testuser"
        mock_user.first_name = "Иван"
        mock_user.last_name = "Петров"
        mock_user.phone = None
        mock_user.avatar_url = None
        mock_user.birth_date = date(1990, 5, 15)
        mock_user.city = "Москва"
        mock_user.bio = "Опытный рыбак"
        mock_user.is_verified = True
        mock_user.role = "user"
        mock_user.created_at = datetime(2024, 1, 1, 12, 0, 0)

        data = UserResponse.model_validate(mock_user)
        assert data.birth_date == date(1990, 5, 15)
        assert data.bio == "Опытный рыбак"
        assert data.city == "Москва"


# ============================================================
# CSRF middleware — graceful degradation tests
# ============================================================

class TestCSRFMiddlewareGracefulDegradation:
    @pytest.fixture
    def mock_app(self):
        return MagicMock()

    @pytest.fixture
    def csrf_middleware(self, mock_app):
        return CSRFMiddleware(mock_app)

    @pytest.mark.asyncio
    async def test_uninitialized_csrf_protection_skips_validation(self, csrf_middleware):
        """
        When CSRF protection is not initialized (Redis unavailable at startup),
        the middleware must NOT return 500. It should skip validation and pass
        the request through — mirroring the graceful degradation in validate_token().
        """
        mock_request = MagicMock()
        mock_request.scope = {"type": "http"}
        mock_request.method = "PUT"
        mock_request.url.path = "/api/v1/users/me"
        mock_request.headers.get.side_effect = (
            lambda h: "Bearer valid_token" if h == "Authorization"
            else "some-csrf-token" if h == "X-CSRF-Token"
            else None
        )
        mock_request.client.host = "127.0.0.1"
        mock_call_next = AsyncMock()

        mock_payload = {"sub": "user-123"}

        with patch("app.middleware.csrf.decode_access_token", return_value=mock_payload):
            with patch(
                "app.middleware.csrf.get_csrf_protection",
                side_effect=RuntimeError("CSRF protection not initialized"),
            ):
                await csrf_middleware.dispatch(mock_request, mock_call_next)

        # Must pass through — no exception, no 500
        mock_call_next.assert_called_once_with(mock_request)

    @pytest.mark.asyncio
    async def test_missing_csrf_token_still_returns_403(self, csrf_middleware):
        """
        Even with graceful degradation for uninitialized protection,
        a missing CSRF token header should still return 403 (not 500).
        The RuntimeError path is only reached when the token IS present.
        """
        from fastapi import HTTPException

        mock_request = MagicMock()
        mock_request.scope = {"type": "http"}
        mock_request.method = "PUT"
        mock_request.url.path = "/api/v1/users/me"
        # No CSRF token header
        mock_request.headers.get.side_effect = (
            lambda h: "Bearer valid_token" if h == "Authorization" else None
        )
        mock_request.client.host = "127.0.0.1"
        mock_call_next = AsyncMock()

        mock_payload = {"sub": "user-123"}

        with patch("app.middleware.csrf.decode_access_token", return_value=mock_payload):
            with pytest.raises(HTTPException) as exc_info:
                await csrf_middleware.dispatch(mock_request, mock_call_next)

        assert exc_info.value.status_code == 403
        assert exc_info.value.detail["code"] == "CSRF_TOKEN_MISSING"

    @pytest.mark.asyncio
    async def test_valid_token_with_initialized_protection_passes(self, csrf_middleware):
        """Happy path: valid CSRF token + initialized protection → request passes."""
        mock_request = MagicMock()
        mock_request.scope = {"type": "http"}
        mock_request.method = "PUT"
        mock_request.url.path = "/api/v1/users/me"
        mock_request.headers.get.side_effect = (
            lambda h: "Bearer valid_token" if h == "Authorization"
            else "valid-csrf-token" if h == "X-CSRF-Token"
            else None
        )
        mock_request.client.host = "127.0.0.1"
        mock_call_next = AsyncMock()

        mock_payload = {"sub": "user-123"}
        mock_csrf_protection = AsyncMock()
        mock_csrf_protection.validate_token = AsyncMock(return_value=True)

        with patch("app.middleware.csrf.decode_access_token", return_value=mock_payload):
            with patch(
                "app.middleware.csrf.get_csrf_protection",
                return_value=mock_csrf_protection,
            ):
                await csrf_middleware.dispatch(mock_request, mock_call_next)

        mock_call_next.assert_called_once_with(mock_request)
        mock_csrf_protection.validate_token.assert_called_once_with(
            "user-123", "valid-csrf-token"
        )
