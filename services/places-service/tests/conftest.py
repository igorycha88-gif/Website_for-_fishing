import os
import pytest
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

os.environ.setdefault("DATABASE_URL", "postgresql+asyncpg://test:test@localhost:5432/test")
os.environ.setdefault("REDIS_URL", "redis://localhost:6379/0")
os.environ.setdefault("SECRET_KEY", "test-secret-key-min-32-characters-long")
os.environ.setdefault("ENVIRONMENT", "test")

from app.core.config import settings  # noqa: E402
from app.core.database import Base  # noqa: E402


@pytest.fixture
async def db():
    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    try:
        async with engine.connect() as conn:
            pass
    except Exception:
        pytest.skip("PostgreSQL not available")
        return

    testing_async_session = sessionmaker(
        engine, class_=AsyncSession, expire_on_commit=False
    )
    async with testing_async_session() as session:
        async with engine.begin() as conn:
            await conn.run_sync(Base.metadata.create_all)

        try:
            await session.execute(text("DELETE FROM favorite_places"))
            await session.execute(text("DELETE FROM fish_types"))
            await session.execute(text("DELETE FROM equipment_types"))
            await session.execute(text("DELETE FROM places"))
            await session.commit()

            yield session
        finally:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.drop_all)

    await engine.dispose()
