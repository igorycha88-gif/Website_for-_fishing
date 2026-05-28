import asyncio
import sys
from app.core.security import get_password_hash
from app.models.user import User
from app.core.database import database
from sqlalchemy import select

async def reset_admin_password():
    if len(sys.argv) < 2:
        print("Usage: python reset_admin.py <new_password>")
        print("Example: python reset_admin.py Admin@NewSecure123!")
        return

    new_password = sys.argv[1]
    if len(new_password) < 12:
        print("Error: Password must be at least 12 characters")
        return

    async with database.async_session() as session:
        result = await session.execute(
            select(User).where(User.role == "admin")
        )
        admin = result.scalar_one_or_none()

        if not admin:
            print("Error: Admin not found. Use create_admin.py to create an admin.")
            return

        admin.password_hash = get_password_hash(new_password)
        await session.commit()

        print("\n======================================")
        print("ADMIN PASSWORD RESET SUCCESSFULLY!")
        print("======================================")
        print(f"Email: {admin.email}")
        print(f"Username: {admin.username}")
        print(f"New password: {new_password}")
        print("======================================")

if __name__ == "__main__":
    asyncio.run(reset_admin_password())
