import pytest
from unittest.mock import AsyncMock, MagicMock
from datetime import datetime, timedelta
from uuid import uuid4
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../../..")))

from app.crud.password_reset_token import PasswordResetTokenCRUD
from app.models.password_reset_token import PasswordResetToken


@pytest.fixture
def mock_db():
    return AsyncMock()


@pytest.fixture
def password_reset_token_crud(mock_db):
    return PasswordResetTokenCRUD(mock_db)


@pytest.fixture
def sample_user_id():
    return str(uuid4())


@pytest.fixture
def sample_token_hash():
    return "hashed_token_example_123456"


@pytest.mark.asyncio
async def test_create_password_reset_token(password_reset_token_crud, mock_db, sample_user_id, sample_token_hash):
    expires_at = datetime.utcnow() + timedelta(hours=1)
    ip_address = "192.168.1.1"
    user_agent = "Mozilla/5.0"
    
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    token = await password_reset_token_crud.create(
        user_id=sample_user_id,
        token_hash=sample_token_hash,
        expires_at=expires_at,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
    assert isinstance(token, PasswordResetToken)


@pytest.mark.asyncio
async def test_create_password_reset_token_minimal(password_reset_token_crud, mock_db, sample_user_id, sample_token_hash):
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    token = await password_reset_token_crud.create(
        user_id=sample_user_id,
        token_hash=sample_token_hash,
        expires_at=expires_at
    )
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
    assert isinstance(token, PasswordResetToken)


@pytest.mark.asyncio
async def test_get_by_token_hash_found(password_reset_token_crud, mock_db, sample_token_hash):
    mock_token = MagicMock(spec=PasswordResetToken)
    mock_token.token_hash = sample_token_hash
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_token
    mock_db.execute.return_value = mock_result
    
    result = await password_reset_token_crud.get_by_token_hash(sample_token_hash)
    
    assert result == mock_token
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_by_token_hash_not_found(password_reset_token_crud, mock_db, sample_token_hash):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    result = await password_reset_token_crud.get_by_token_hash(sample_token_hash)
    
    assert result is None
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_mark_as_used_success(password_reset_token_crud, mock_db):
    token_id = uuid4()
    ip_address = "192.168.1.1"
    user_agent = "Mozilla/5.0"
    
    mock_result = MagicMock()
    mock_result.rowcount = 1
    mock_db.execute.return_value = mock_result
    mock_db.commit = AsyncMock()
    
    result = await password_reset_token_crud.mark_as_used(
        token_id=token_id,
        ip_address=ip_address,
        user_agent=user_agent
    )
    
    assert result is True
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_mark_as_used_not_found(password_reset_token_crud, mock_db):
    token_id = uuid4()
    
    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_db.execute.return_value = mock_result
    mock_db.commit = AsyncMock()
    
    result = await password_reset_token_crud.mark_as_used(token_id=token_id)
    
    assert result is False
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_invalidate_user_tokens(password_reset_token_crud, mock_db, sample_user_id):
    mock_result = MagicMock()
    mock_result.rowcount = 3
    mock_db.execute.return_value = mock_result
    mock_db.commit = AsyncMock()
    
    count = await password_reset_token_crud.invalidate_user_tokens(sample_user_id)
    
    assert count == 3
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_invalidate_user_tokens_no_tokens(password_reset_token_crud, mock_db, sample_user_id):
    mock_result = MagicMock()
    mock_result.rowcount = 0
    mock_db.execute.return_value = mock_result
    mock_db.commit = AsyncMock()
    
    count = await password_reset_token_crud.invalidate_user_tokens(sample_user_id)
    
    assert count == 0
    mock_db.execute.assert_called_once()
    mock_db.commit.assert_called_once()


@pytest.mark.asyncio
async def test_get_active_token_by_user_found(password_reset_token_crud, mock_db, sample_user_id):
    mock_token = MagicMock(spec=PasswordResetToken)
    mock_token.user_id = sample_user_id
    mock_token.used = False
    mock_token.expires_at = datetime.utcnow() + timedelta(hours=1)
    
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = mock_token
    mock_db.execute.return_value = mock_result
    
    result = await password_reset_token_crud.get_active_token_by_user(sample_user_id)
    
    assert result == mock_token
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_get_active_token_by_user_not_found(password_reset_token_crud, mock_db, sample_user_id):
    mock_result = MagicMock()
    mock_result.scalar_one_or_none.return_value = None
    mock_db.execute.return_value = mock_result
    
    result = await password_reset_token_crud.get_active_token_by_user(sample_user_id)
    
    assert result is None
    mock_db.execute.assert_called_once()


@pytest.mark.asyncio
async def test_create_with_uuid_object(password_reset_token_crud, mock_db, sample_token_hash):
    user_id = uuid4()
    expires_at = datetime.utcnow() + timedelta(hours=1)
    
    mock_db.add = MagicMock()
    mock_db.commit = AsyncMock()
    mock_db.refresh = AsyncMock()
    
    token = await password_reset_token_crud.create(
        user_id=user_id,
        token_hash=sample_token_hash,
        expires_at=expires_at
    )
    
    mock_db.add.assert_called_once()
    mock_db.commit.assert_called_once()
    mock_db.refresh.assert_called_once()
    assert isinstance(token, PasswordResetToken)
