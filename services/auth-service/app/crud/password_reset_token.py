import sys
import os
from typing import Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, update
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared-utils")))

from app.models.password_reset_token import PasswordResetToken


class PasswordResetTokenCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: str,
        token_hash: str,
        expires_at: datetime,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> PasswordResetToken:
        password_reset_token = PasswordResetToken(
            user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
            token_hash=token_hash,
            expires_at=expires_at,
            ip_address=ip_address,
            user_agent=user_agent
        )
        self.db.add(password_reset_token)
        await self.db.commit()
        await self.db.refresh(password_reset_token)
        return password_reset_token

    async def get_by_token_hash(self, token_hash: str) -> Optional[PasswordResetToken]:
        result = await self.db.execute(
            select(PasswordResetToken).where(PasswordResetToken.token_hash == token_hash)
        )
        return result.scalar_one_or_none()

    async def mark_as_used(
        self,
        token_id: UUID,
        ip_address: Optional[str] = None,
        user_agent: Optional[str] = None
    ) -> bool:
        result = await self.db.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.id == token_id)
            .values(used=True, used_at=datetime.utcnow(), ip_address=ip_address, user_agent=user_agent)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def invalidate_user_tokens(self, user_id: str) -> int:
        uuid_user_id = UUID(user_id) if isinstance(user_id, str) else user_id
        result = await self.db.execute(
            update(PasswordResetToken)
            .where(PasswordResetToken.user_id == uuid_user_id)
            .where(PasswordResetToken.used == False)
            .values(used=True, used_at=datetime.utcnow())
        )
        await self.db.commit()
        return result.rowcount

    async def get_active_token_by_user(self, user_id: str) -> Optional[PasswordResetToken]:
        uuid_user_id = UUID(user_id) if isinstance(user_id, str) else user_id
        result = await self.db.execute(
            select(PasswordResetToken)
            .where(PasswordResetToken.user_id == uuid_user_id)
            .where(PasswordResetToken.used == False)
            .where(PasswordResetToken.expires_at > datetime.utcnow())
            .order_by(PasswordResetToken.created_at.desc())
        )
        return result.scalar_one_or_none()
