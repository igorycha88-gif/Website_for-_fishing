import pytest
import asyncio
import time
import os
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine, async_sessionmaker
from sqlalchemy import text
from httpx import AsyncClient, ASGITransport
from decimal import Decimal
import uuid

from pytest_postgresql import factories

from app.models.place import Place
from app.models.user import User
from app.core.security import create_access_token
from app.crud.place import PlaceCRUD
from app.schemas.place import PlaceCreate, PlaceUpdate
from app.core.config import settings


TEST_DATABASE_URL = os.getenv(
    "TEST_DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres_password@localhost:5433/fishing_test_db"
)


@pytest.fixture(scope="session")
def postgresql_engine():
    """
    Создает engine для PostgreSQL
    Один engine на сессию для скорости
    """
    engine = create_async_engine(
        TEST_DATABASE_URL,
        echo=False,
        future=True
    )

    yield engine

    asyncio.run(engine.dispose())


@pytest.fixture
async def db_session(postgresql_engine):
    """
    Создает и уничтожает таблицы для каждого теста
    Обеспечивает изоляцию между тестами
    """
    async_session_maker = async_sessionmaker(
        postgresql_engine,
        class_=AsyncSession,
        expire_on_commit=False
    )

    # Создаем таблицы перед тестом
    async with postgresql_engine.begin() as conn:
        try:
            await conn.run_sync(Place.metadata.drop_all)
            await conn.run_sync(User.metadata.drop_all)
        except Exception:
            pass

        await conn.run_sync(Place.metadata.create_all)
        await conn.run_sync(User.metadata.create_all)

    # Выдаем сессию тесту
    async with async_session_maker() as session:
        yield session

    # Удаляем таблицы после теста
    async with postgresql_engine.begin() as conn:
        try:
            await conn.run_sync(Place.metadata.drop_all)
            await conn.run_sync(User.metadata.drop_all)
        except Exception:
            pass


@pytest.fixture
def sample_place_data():
    return PlaceCreate(
        title="Тестовое место",
        description="Описание тестового места для рыбалки",
        latitude=Decimal("55.7558"),
        longitude=Decimal("37.6173"),
        address="Москва, Россия",
        city="Москва",
        region="Московская область",
        price_per_day=Decimal("1000.00"),
        max_people=5,
        facilities=["parking", "toilet"],
        fish_types=["carp", "bream"],
        images=["https://example.com/image1.jpg"],
        is_public=False,
        visit_date=None
    )


@pytest.fixture
async def sample_user(db_session: AsyncSession):
    from app.core.security import get_password_hash

    user = User(
        email="test@example.com",
        username="testuser",
        password_hash=get_password_hash("testpassword123"),
        is_verified=True
    )
    db_session.add(user)
    await db_session.commit()
    await db_session.refresh(user)
    return user


@pytest.fixture
def auth_headers(sample_user):
    token = create_access_token(data={"sub": str(sample_user.id)})
    return {"Authorization": f"Bearer {token}"}


@pytest.fixture
async def client(db_session: AsyncSession):
    from app.main import app
    from app.core.database import get_db

    async def override_get_db():
        yield db_session

    app.dependency_overrides[get_db] = override_get_db

    transport = ASGITransport(app=app)
    async with AsyncClient(transport=transport, base_url="http://test") as ac:
        yield ac

    app.dependency_overrides.clear()
