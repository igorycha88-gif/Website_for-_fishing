import asyncio
import sys
import os
from sqlalchemy import text
from app.core.database import database

async def migrate():
    """Add role column to users table if it doesn't exist"""
    async with database.engine.begin() as conn:
        try:
            # Check if column exists
            result = await conn.execute(
                text("""
                    SELECT column_name 
                    FROM information_schema.columns 
                    WHERE table_name='users' AND column_name='role'
                """)
            )
            
            column_exists = result.scalar() is not None
            
            if not column_exists:
                print("Adding 'role' column to users table...")
                await conn.execute(
                    text("""
                        ALTER TABLE users 
                        ADD COLUMN role VARCHAR(50) NOT NULL DEFAULT 'user'
                    """)
                )
                print("✓ 'role' column added successfully")
            else:
                print("✓ 'role' column already exists")
                
        except Exception as e:
            print(f"✗ Error: {e}")
            sys.exit(1)

if __name__ == "__main__":
    asyncio.run(migrate())
