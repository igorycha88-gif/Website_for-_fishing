import sys
import os
from datetime import datetime, timedelta
from typing import Optional
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared-utils")))

from app.models.email_verification_code import EmailVerificationCode


class EmailVerificationCodeCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, email: str, code: str, expire_minutes: int) -> EmailVerificationCode:
        verification_code = EmailVerificationCode(
            email=email,
            code=code,
            expires_at=datetime.utcnow() + timedelta(minutes=expire_minutes)
        )
        self.db.add(verification_code)
        await self.db.commit()
        await self.db.refresh(verification_code)
        return verification_code

    async def get_by_email(self, email: str) -> Optional[EmailVerificationCode]:
        result = await self.db.execute(
            select(EmailVerificationCode).where(EmailVerificationCode.email == email)
        )
        return result.scalar_one_or_none()

    async def get_valid_code(self, email: str, code: str) -> Optional[EmailVerificationCode]:
        result = await self.db.execute(
            select(EmailVerificationCode).where(
                EmailVerificationCode.email == email,
                EmailVerificationCode.code == code,
                EmailVerificationCode.expires_at > datetime.utcnow(),
                EmailVerificationCode.attempts < 3
            )
        )
        return result.scalar_one_or_none()

    async def increment_attempts(self, email: str) -> Optional[EmailVerificationCode]:
        verification_code = await self.get_by_email(email)
        if verification_code:
            verification_code.attempts += 1
            await self.db.commit()
            await self.db.refresh(verification_code)
        return verification_code

    async def delete_by_email(self, email: str) -> bool:
        result = await self.db.execute(
            delete(EmailVerificationCode).where(EmailVerificationCode.email == email)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def delete_expired(self) -> int:
        result = await self.db.execute(
            delete(EmailVerificationCode).where(EmailVerificationCode.expires_at < datetime.utcnow())
        )
        await self.db.commit()
        return result.rowcount
