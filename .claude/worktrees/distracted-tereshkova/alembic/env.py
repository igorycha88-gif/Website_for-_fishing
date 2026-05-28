"""
Alembic env.py — единая точка миграций для всех сервисов.

Объединяет ORM-модели из auth-service и places-service в одну metadata.
Использует async-режим (asyncpg), не требует psycopg2.

Стратегия: создаём свою Base (DeclarativeBase) и подставляем её как
stub-модуль `app.core.database`, чтобы модели сервисов при импорте
регистрировались в единой metadata без side-effects (engine, settings).
"""
import os
import sys
import asyncio
import types
import importlib.util
from logging.config import fileConfig

from alembic import context
from sqlalchemy import pool
from sqlalchemy.ext.asyncio import create_async_engine
from sqlalchemy.orm import DeclarativeBase

# --- Единая Base для Alembic ---


class Base(DeclarativeBase):
    pass


# --- sys.path + stub setup ---
PROJECT_ROOT = os.path.abspath(os.path.join(os.path.dirname(__file__), ".."))
AUTH_SERVICE_PATH = os.path.join(PROJECT_ROOT, "services", "auth-service")
PLACES_SERVICE_PATH = os.path.join(PROJECT_ROOT, "services", "places-service")

sys.path.insert(0, AUTH_SERVICE_PATH)

# Импортируем реальные пакеты app и app.core из auth-service,
# но подменяем app.core.database stub-модулем с нашей Base.
# Это избегает side-effects (создание engine, загрузка Settings).
import app  # noqa: E402
import app.core  # noqa: E402

_stub = types.ModuleType("app.core.database")
_stub.Base = Base
sys.modules["app.core.database"] = _stub

# --- Импорт моделей ---
# Все модели делают `from app.core.database import Base` —
# теперь это наш stub, все регистрируются в единой Base.metadata.

# Auth-service
from app.models.user import User  # noqa: E402, F401
from app.models.email_verification_code import EmailVerificationCode  # noqa: E402, F401
from app.models.password_reset_code import PasswordResetCode  # noqa: E402, F401

# Places-service (через importlib — другой путь на диске, тот же stub Base)
_place_path = os.path.join(PLACES_SERVICE_PATH, "app", "models", "place.py")
_spec = importlib.util.spec_from_file_location("places_place", _place_path)
_place_module = importlib.util.module_from_spec(_spec)
_spec.loader.exec_module(_place_module)
Place = _place_module.Place  # noqa: F841

# --- Metadata ---
target_metadata = Base.metadata

# --- Alembic config ---
config = context.config
if config.config_file_name is not None:
    fileConfig(config.config_file_name)


def get_database_url() -> str:
    """DATABASE_URL из env или alembic.ini."""
    url = os.environ.get("DATABASE_URL")
    if url:
        return url
    url = config.get_main_option("sqlalchemy.url")
    if url:
        return url
    raise RuntimeError(
        "DATABASE_URL не задан. Установите переменную окружения DATABASE_URL "
        "или укажите sqlalchemy.url в alembic.ini"
    )


def run_migrations_offline() -> None:
    """Генерация SQL без подключения к БД."""
    url = get_database_url()
    context.configure(
        url=url,
        target_metadata=target_metadata,
        literal_binds=True,
        dialect_opts={"paramstyle": "named"},
    )
    with context.begin_transaction():
        context.run_migrations()


def do_run_migrations(connection) -> None:
    """Выполнение миграций через sync-connection (вызывается из async)."""
    context.configure(
        connection=connection,
        target_metadata=target_metadata,
    )
    with context.begin_transaction():
        context.run_migrations()


async def run_async_migrations() -> None:
    """Async-режим миграций через asyncpg."""
    database_url = get_database_url()
    connectable = create_async_engine(
        database_url,
        poolclass=pool.NullPool,
    )
    async with connectable.connect() as connection:
        await connection.run_sync(do_run_migrations)
    await connectable.dispose()


def run_migrations_online() -> None:
    """Запуск async-миграций."""
    asyncio.run(run_async_migrations())


if context.is_offline_mode():
    run_migrations_offline()
else:
    run_migrations_online()
