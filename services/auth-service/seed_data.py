"""Seed data for Auth Service - creates test user for login"""

import asyncio
from sqlalchemy.ext.asyncio import AsyncSession, create_async_engine
from sqlalchemy.orm import sessionmaker
from sqlalchemy import text

from app.core.config import settings
from app.core.security import get_password_hash


async def seed_users():
    """Create test users for development and testing"""

    engine = create_async_engine(settings.DATABASE_URL, echo=False)
    async_session = sessionmaker(engine, class_=AsyncSession, expire_on_commit=False)

    async with async_session() as session:
        # Check if users already exist
        result = await session.execute(text("SELECT COUNT(*) FROM users"))
        count = result.scalar()

        if count > 0:
            print(f"✓ Users table already has {count} records - skipping seed")
            return

        print("Seeding users table...")

        # Create test user
        test_password = get_password_hash("test123")

        await session.execute(
            text("""
                INSERT INTO users (email, username, password_hash, first_name, last_name, is_verified)
                VALUES (:email, :username, :password_hash, :first_name, :last_name, true)
            """),
            {
                "email": "test@rybalka.ru",
                "username": "testuser",
                "password_hash": test_password,
                "first_name": "Тестовый",
                "last_name": "Пользователь",
            },
        )

        await session.commit()
        print(f"✓ Seeded 1 test user: test@rybalka.ru / test123")


if __name__ == "__main__":
    asyncio.run(seed_users())
