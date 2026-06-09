"""
Tests for startup migration runner (apply_pending_migrations).

Covers Bug Fix:
  - POST /api/v1/auth/login 500 when auth-service is rebuilt with new User model
    (birth_date, bio) but migration 006 has not yet been applied to the database.

The fix: apply_pending_migrations() in main.py lifespan executes
  ALTER TABLE users ADD COLUMN IF NOT EXISTS birth_date DATE
  ALTER TABLE users ADD COLUMN IF NOT EXISTS bio TEXT
at every startup.  IF NOT EXISTS makes it idempotent.
"""
import pytest
from unittest.mock import AsyncMock, MagicMock, patch, call
import sys
import os

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "..")))

from app.main import apply_pending_migrations


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------

def _make_mock_engine() -> MagicMock:
    """Return a mock async engine whose begin() context manager works."""
    mock_conn = AsyncMock()

    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(return_value=mock_conn)
    mock_ctx.__aexit__ = AsyncMock(return_value=None)

    mock_engine = MagicMock()
    mock_engine.begin = MagicMock(return_value=mock_ctx)
    return mock_engine, mock_conn


# ---------------------------------------------------------------------------
# Happy path
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_pending_migrations_executes_all_statements():
    """apply_pending_migrations must execute both ALTER TABLE statements."""
    mock_engine, mock_conn = _make_mock_engine()

    with patch("app.main.database") as mock_database:
        mock_database.engine = mock_engine
        await apply_pending_migrations()

    assert mock_conn.execute.call_count == 2, (
        "Expected exactly 2 SQL statements (birth_date and bio)"
    )


@pytest.mark.asyncio
async def test_apply_pending_migrations_uses_if_not_exists():
    """Each SQL statement must use IF NOT EXISTS to be idempotent."""
    mock_engine, mock_conn = _make_mock_engine()

    executed_sql: list[str] = []

    async def capture_execute(stmt):
        executed_sql.append(str(stmt))

    mock_conn.execute = capture_execute

    with patch("app.main.database") as mock_database:
        mock_database.engine = mock_engine
        await apply_pending_migrations()

    for sql in executed_sql:
        assert "IF NOT EXISTS" in sql.upper(), (
            f"SQL statement must use IF NOT EXISTS for idempotency, got: {sql!r}"
        )


@pytest.mark.asyncio
async def test_apply_pending_migrations_includes_birth_date():
    """Migration must add birth_date column."""
    mock_engine, mock_conn = _make_mock_engine()

    executed_sql: list[str] = []

    async def capture_execute(stmt):
        executed_sql.append(str(stmt))

    mock_conn.execute = capture_execute

    with patch("app.main.database") as mock_database:
        mock_database.engine = mock_engine
        await apply_pending_migrations()

    birth_date_found = any("birth_date" in sql.lower() for sql in executed_sql)
    assert birth_date_found, "Migration must include birth_date column"


@pytest.mark.asyncio
async def test_apply_pending_migrations_includes_bio():
    """Migration must add bio column."""
    mock_engine, mock_conn = _make_mock_engine()

    executed_sql: list[str] = []

    async def capture_execute(stmt):
        executed_sql.append(str(stmt))

    mock_conn.execute = capture_execute

    with patch("app.main.database") as mock_database:
        mock_database.engine = mock_engine
        await apply_pending_migrations()

    bio_found = any("bio" in sql.lower() for sql in executed_sql)
    assert bio_found, "Migration must include bio column"


@pytest.mark.asyncio
async def test_apply_pending_migrations_targets_users_table():
    """Migrations must target the users table."""
    mock_engine, mock_conn = _make_mock_engine()

    executed_sql: list[str] = []

    async def capture_execute(stmt):
        executed_sql.append(str(stmt))

    mock_conn.execute = capture_execute

    with patch("app.main.database") as mock_database:
        mock_database.engine = mock_engine
        await apply_pending_migrations()

    for sql in executed_sql:
        assert "users" in sql.lower(), (
            f"Migration must target 'users' table, got: {sql!r}"
        )


# ---------------------------------------------------------------------------
# Idempotency
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_pending_migrations_idempotent_on_second_call():
    """
    Calling apply_pending_migrations twice must not raise — IF NOT EXISTS
    guarantees the second run is a no-op in PostgreSQL.
    """
    mock_engine, mock_conn = _make_mock_engine()

    with patch("app.main.database") as mock_database:
        mock_database.engine = mock_engine
        await apply_pending_migrations()
        await apply_pending_migrations()

    # 2 calls × 2 statements each = 4
    assert mock_conn.execute.call_count == 4


# ---------------------------------------------------------------------------
# Graceful degradation — DB unavailable at startup
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_apply_pending_migrations_does_not_raise_on_db_error():
    """
    If the database is unavailable at startup (e.g. PostgreSQL not yet ready),
    apply_pending_migrations must catch the exception and log an error instead
    of crashing the service — login must still be attempted once DB recovers.
    """
    mock_engine = MagicMock()
    mock_ctx = AsyncMock()
    mock_ctx.__aenter__ = AsyncMock(side_effect=Exception("Connection refused"))
    mock_ctx.__aexit__ = AsyncMock(return_value=None)
    mock_engine.begin = MagicMock(return_value=mock_ctx)

    with patch("app.main.database") as mock_database:
        mock_database.engine = mock_engine
        # Must NOT raise
        try:
            await apply_pending_migrations()
        except Exception as exc:
            pytest.fail(
                f"apply_pending_migrations raised an exception when DB is unavailable: {exc}"
            )


@pytest.mark.asyncio
async def test_apply_pending_migrations_does_not_raise_on_execute_error():
    """
    If execute() raises (e.g. permission denied), the exception must be
    caught gracefully — service startup continues.
    """
    mock_engine, mock_conn = _make_mock_engine()
    mock_conn.execute = AsyncMock(side_effect=Exception("permission denied for table users"))

    with patch("app.main.database") as mock_database:
        mock_database.engine = mock_engine
        try:
            await apply_pending_migrations()
        except Exception as exc:
            pytest.fail(
                f"apply_pending_migrations raised an exception on execute error: {exc}"
            )


# ---------------------------------------------------------------------------
# Integration: lifespan calls apply_pending_migrations first
# ---------------------------------------------------------------------------


@pytest.mark.asyncio
async def test_lifespan_calls_apply_pending_migrations():
    """
    The lifespan context manager must call apply_pending_migrations()
    before initialising rate limiting and CSRF protection.
    This ensures the DB schema is ready before any request is processed.
    """
    call_order: list[str] = []

    async def mock_migrations():
        call_order.append("migrations")

    async def mock_rate_limiter(app):
        call_order.append("rate_limiter")

    async def mock_csrf(redis):
        call_order.append("csrf")

    mock_settings = MagicMock()
    mock_settings.RATE_LIMIT_ENABLED = True
    mock_settings.CSRF_ENABLED = True

    with (
        patch("app.main.apply_pending_migrations", side_effect=mock_migrations),
        patch("app.main.init_rate_limiter", side_effect=mock_rate_limiter),
        patch("app.main.init_csrf_protection", side_effect=mock_csrf),
        patch("app.main.settings", mock_settings),
        patch("app.main.redis_client", MagicMock()),
    ):
        from app.main import lifespan, app as fastapi_app

        async with lifespan(fastapi_app):
            pass

    assert call_order[0] == "migrations", (
        f"apply_pending_migrations must be called first, got order: {call_order}"
    )
    assert "rate_limiter" in call_order
    assert "csrf" in call_order
