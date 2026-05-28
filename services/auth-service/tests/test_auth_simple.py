import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import (
    create_access_token,
    decode_access_token,
    verify_password,
    get_password_hash,
)


@pytest.mark.asyncio
async def test_create_access_token():
    data = {"sub": "user-123", "role": "user"}
    token = create_access_token(data)

    assert isinstance(token, str)
    assert len(token) > 0


@pytest.mark.asyncio
async def test_decode_valid_token():
    data = {"sub": "user-123", "role": "user"}
    token = create_access_token(data)

    decoded = decode_access_token(token)

    assert decoded is not None
    assert decoded["sub"] == "user-123"
    assert decoded["role"] == "user"


@pytest.mark.asyncio
async def test_decode_invalid_token():
    decoded = decode_access_token("invalid.token.here")

    assert decoded is None


@pytest.mark.asyncio
async def test_hash_and_verify_password():
    password = "TestPassword123"
    hashed = get_password_hash(password)

    assert hashed != password
    assert verify_password(password, hashed) is True
    assert verify_password("WrongPassword", hashed) is False


@pytest.mark.asyncio
async def test_verify_password_with_invalid_hash():
    from passlib.exc import UnknownHashError

    try:
        result = verify_password("password", "invalid_hash")
        assert result is False
    except UnknownHashError:
        pass  # Invalid hash format is expected


@pytest.mark.asyncio
async def test_create_access_token_with_expiration():
    from datetime import timedelta

    data = {"sub": "user-123", "role": "user"}
    token = create_access_token(data, expires_delta=timedelta(minutes=5))

    assert isinstance(token, str)
    assert len(token) > 0
