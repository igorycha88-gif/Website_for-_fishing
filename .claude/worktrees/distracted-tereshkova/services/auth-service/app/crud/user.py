import sys
import os
import uuid
from typing import Optional
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared-utils")))

from app.models.user import User


class UserCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, email: str, username: str, password_hash: str) -> User:
        user = User(
            email=email,
            username=username,
            password_hash=password_hash
        )
        self.db.add(user)
        await self.db.flush()
        await self.db.refresh(user)
        return user

    async def get_by_id(self, user_id: str) -> Optional[User]:
        try:
            user_uuid = uuid.UUID(user_id)
        except ValueError:
            return None
        result = await self.db.execute(select(User).where(User.id == user_uuid))
        return result.scalar_one_or_none()

    async def get_by_email(self, email: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.email == email))
        return result.scalar_one_or_none()

    async def get_by_username(self, username: str) -> Optional[User]:
        result = await self.db.execute(select(User).where(User.username == username))
        return result.scalar_one_or_none()

    async def verify_email(self, email: str) -> Optional[User]:
        user = await self.get_by_email(email)
        if user:
            await self.db.execute(
                update(User)
                .where(User.email == email)
                .values(is_verified=True)
            )
            await self.db.flush()
            await self.db.refresh(user)
        return user

    async def reset_password(self, email: str, new_password_hash: str) -> Optional[User]:
        user = await self.get_by_email(email)
        if user:
            await self.db.execute(
                update(User)
                .where(User.email == email)
                .values(password_hash=new_password_hash)
            )
            await self.db.flush()
            await self.db.refresh(user)
        return user

    async def update(self, user_id: str, **kwargs) -> Optional[User]:
        user = await self.get_by_id(user_id)
        if user:
            for key, value in kwargs.items():
                if hasattr(user, key):
                    setattr(user, key, value)
            await self.db.flush()
            await self.db.refresh(user)
        return user

    async def delete(self, user_id: str) -> bool:
        user = await self.get_by_id(user_id)
        if user:
            await self.db.delete(user)
            await self.db.flush()
            return True
        return False
