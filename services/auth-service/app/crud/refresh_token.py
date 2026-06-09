import sys
import os
from typing import Optional
from datetime import datetime
from uuid import UUID
from sqlalchemy import select, update, delete
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared-utils")))

from app.models.refresh_token import RefreshToken


class RefreshTokenCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(
        self,
        user_id: str,
        token: str,
        jti: str,
        expires_at: datetime
    ) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=UUID(user_id) if isinstance(user_id, str) else user_id,
            token=token,
            jti=jti,
            expires_at=expires_at
        )
        self.db.add(refresh_token)
        await self.db.commit()
        await self.db.refresh(refresh_token)
        return refresh_token

    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.token == token))
        return result.scalar_one_or_none()

    async def get_by_jti(self, jti: str) -> Optional[RefreshToken]:
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.jti == jti))
        return result.scalar_one_or_none()

    async def revoke(self, jti: str, replaced_by: Optional[str] = None) -> bool:
        result = await self.db.execute(
            update(RefreshToken)
            .where(RefreshToken.jti == jti)
            .values(revoked=True, revoked_at=datetime.utcnow(), replaced_by=replaced_by)
        )
        await self.db.commit()
        return result.rowcount > 0

    async def is_revoked(self, jti: str) -> bool:
        refresh_token = await self.get_by_jti(jti)
        if not refresh_token:
            return True
        return refresh_token.revoked

    async def delete_by_token(self, token: str) -> bool:
        refresh_token = await self.get_by_token(token)
        if refresh_token:
            await self.db.delete(refresh_token)
            await self.db.commit()
            return True
        return False

    async def delete_by_user_id(self, user_id: str) -> bool:
        uuid_user_id = UUID(user_id) if isinstance(user_id, str) else user_id
        result = await self.db.execute(
            delete(RefreshToken).where(RefreshToken.user_id == uuid_user_id)
        )
        await self.db.commit()
        return result.rowcount > 0
