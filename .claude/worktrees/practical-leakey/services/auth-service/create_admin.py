import asyncio
import os
import sys
from app.core.security import get_password_hash
from app.models.user import User
from app.core.database import database
from sqlalchemy import select

async def create_admin():
    admin_email = os.getenv("ADMIN_EMAIL", "admin@fishmap.ru")
    admin_password = os.getenv("ADMIN_PASSWORD")

    if admin_password:
        password = admin_password
    else:
        print("ADMIN_PASSWORD not set in environment. Generating secure password...")
        import secrets
        password = secrets.token_urlsafe(16)
        print(f"\nGenerated password: {password}")
        print("IMPORTANT: Save this password securely!")

    if len(password) < 12:
        print("Error: Password must be at least 12 characters")
        return

    async with database.async_session() as session:
        result = await session.execute(
            select(User).where(User.role == "admin")
        )
        existing_admins = result.scalars().all()

        if existing_admins:
            print(f"Found {len(existing_admins)} existing admin(s)!")
            for admin in existing_admins:
                print(f"  - Email: {admin.email}, Username: {admin.username}, ID: {admin.id}")
            print("\nTo create a new admin, delete the existing one(s) first using delete_admin.py")
            return

        password_hash = get_password_hash(password[:72])

        admin = User(
            email=admin_email,
            username="admin",
            password_hash=password_hash,
            is_verified=True,
            is_active=True,
            role="admin"
        )

        session.add(admin)
        await session.commit()
        await session.refresh(admin)

        print("\n======================================")
        print("ADMIN CREATED SUCCESSFULLY!")
        print("======================================")
        print(f"Email: {admin_email}")
        print(f"Username: admin")
        print(f"Password: {password}")
        print(f"User ID: {admin.id}")
        print("\n======================================")
        print("IMPORTANT: Save these credentials securely!")
        print("======================================")

if __name__ == "__main__":
    asyncio.run(create_admin())
