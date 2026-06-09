from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, delete, update
from sqlalchemy.ext.asyncio import AsyncSession
from app.models.password_reset_code import PasswordResetCode


class PasswordResetCodeCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, email: str, code: str, expire_minutes: int) -> PasswordResetCode:
        reset_code = PasswordResetCode(
            email=email,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=expire_minutes)
        )
        self.db.add(reset_code)
        await self.db.flush()
        await self.db.refresh(reset_code)
        return reset_code

    async def get_by_email(self, email: str) -> Optional[PasswordResetCode]:
        result = await self.db.execute(
            select(PasswordResetCode).where(PasswordResetCode.email == email)
        )
        return result.scalar_one_or_none()

    async def get_valid_code(self, email: str, code: str) -> Optional[PasswordResetCode]:
        result = await self.db.execute(
            select(PasswordResetCode).where(
                PasswordResetCode.email == email,
                PasswordResetCode.code == code,
                PasswordResetCode.expires_at > datetime.utcnow(),
                PasswordResetCode.attempts < 3
            )
        )
        return result.scalar_one_or_none()

    async def increment_attempts(self, email: str) -> Optional[PasswordResetCode]:
        reset_code = await self.get_by_email(email)
        if reset_code:
            await self.db.execute(
                update(PasswordResetCode)
                .where(PasswordResetCode.email == email)
                .values(attempts=PasswordResetCode.attempts + 1)
            )
            await self.db.flush()
            await self.db.refresh(reset_code)
        return reset_code

    async def delete_by_email(self, email: str) -> bool:
        result = await self.db.execute(
            delete(PasswordResetCode).where(PasswordResetCode.email == email)
        )
        await self.db.flush()
        return result.rowcount > 0

    async def delete_expired(self) -> int:
        result = await self.db.execute(
            delete(PasswordResetCode).where(PasswordResetCode.expires_at < datetime.utcnow())
        )
        await self.db.flush()
        return result.rowcount
