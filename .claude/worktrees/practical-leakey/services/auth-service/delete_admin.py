import asyncio
from app.core.database import database
from app.models.user import User
from sqlalchemy import select

async def delete_admin():
    async with database.async_session() as session:
        result = await session.execute(
            select(User).where(User.role == "admin")
        )
        admins = result.scalars().all()

        if not admins:
            print("Error: Admin not found")
            return

        if len(admins) > 1:
            print(f"Found {len(admins)} admins. Deleting all of them...")
            confirm = input(f"\nAre you sure you want to delete ALL {len(admins)} admin(s)? (yes/no): ")
        else:
            admin = admins[0]
            print(f"Found admin: {admin.email} ({admin.username})")
            print(f"User ID: {admin.id}")
            confirm = input("\nAre you sure you want to delete this admin? (yes/no): ")

        if confirm.lower() != "yes":
            print("\nCancelled")
            return

        for admin in admins:
            await session.delete(admin)
        await session.commit()

        print("\n======================================")
        print(f"ADMIN(S) DELETED SUCCESSFULLY! ({len(admins)} admin(s) removed)")
        print("======================================")
        print("You can now create a new admin using create_admin.py")
        print("======================================")

if __name__ == "__main__":
    asyncio.run(delete_admin())
