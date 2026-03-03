import pytest
from unittest.mock import AsyncMock, patch, MagicMock
import sys
import os
from datetime import datetime, timedelta

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.core.security import (
    create_access_token,
    create_refresh_token,
    decode_access_token,
    get_password_hash,
)


class TestJWTTokenFormat:
    def test_access_token_contains_jti(self):
        user_id = "test-user-id"
        token_version = 1
        
        token = create_access_token(
            data={"sub": user_id, "role": "user"},
            token_version=token_version
        )
        
        payload = decode_access_token(token)
        
        assert payload is not None
        assert "jti" in payload
        assert "type" in payload
        assert payload["type"] == "access"
        assert "ver" in payload
        assert payload["ver"] == token_version
        assert "exp" in payload
        assert "iat" in payload

    def test_refresh_token_contains_jti(self):
        user_id = "test-user-id"
        token_version = 1
        
        token = create_refresh_token(
            data={"sub": user_id},
            token_version=token_version
        )
        
        payload = decode_access_token(token)
        
        assert payload is not None
        assert "jti" in payload
        assert "type" in payload
        assert payload["type"] == "refresh"
        assert "ver" in payload
        assert payload["ver"] == token_version
        assert "exp" in payload
        assert "iat" in payload

    def test_tokens_have_unique_jti(self):
        user_id = "test-user-id"
        token_version = 1
        
        token1 = create_access_token(
            data={"sub": user_id, "role": "user"},
            token_version=token_version
        )
        token2 = create_access_token(
            data={"sub": user_id, "role": "user"},
            token_version=token_version
        )
        
        payload1 = decode_access_token(token1)
        payload2 = decode_access_token(token2)
        
        assert payload1["jti"] != payload2["jti"]
    
    def test_access_token_expires_correctly(self):
        user_id = "test-user-id"
        token_version = 1
        
        token = create_access_token(
            data={"sub": user_id, "role": "user"},
            token_version=token_version
        )
        
        payload = decode_access_token(token)
        
        assert payload is not None
        assert "exp" in payload
        exp = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()
        expected_exp = now + timedelta(minutes=30)
        delta = abs((exp - expected_exp).total_seconds())
        assert delta < 5

    def test_refresh_token_expires_correctly(self):
        user_id = "test-user-id"
        token_version = 1
        
        token = create_refresh_token(
            data={"sub": user_id},
            token_version=token_version
        )
        
        payload = decode_access_token(token)
        
        assert payload is not None
        assert "exp" in payload
        exp = datetime.utcfromtimestamp(payload["exp"])
        now = datetime.utcnow()
        expected_exp = now + timedelta(days=7)
        delta = abs((exp - expected_exp).total_seconds())
        assert delta < 5

    def test_token_version_included_correctly(self):
        user_id = "test-user-id"
        token_version = 5
        
        token = create_access_token(
            data={"sub": user_id, "role": "user"},
            token_version=token_version
        )
        
        payload = decode_access_token(token)
        
        assert payload is not None
        assert payload["ver"] == token_version

    def test_password_hash_works(self):
        password = "testpassword123"
        hashed = get_password_hash(password)
        
        assert hashed != password
        assert len(hashed) > 0
    
    def test_decode_invalid_token_returns_none(self):
        invalid_token = "invalid.token.here"
        
        payload = decode_access_token(invalid_token)
        
        assert payload is None
    
    def test_token_contains_user_data(self):
        user_id = "test-user-123"
        role = "admin"
        token_version = 2
        
        token = create_access_token(
            data={"sub": user_id, "role": role},
            token_version=token_version
        )
        
        payload = decode_access_token(token)
        
        assert payload is not None
        assert payload["sub"] == user_id
        assert payload["role"] == role
