import sys
import os
from typing import Optional
from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), "../../../shared-utils")))

from app.models.refresh_token import RefreshToken


class RefreshTokenCRUD:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def create(self, user_id: str, token: str, expires_at) -> RefreshToken:
        refresh_token = RefreshToken(
            user_id=user_id,
            token=token,
            expires_at=expires_at
        )
        self.db.add(refresh_token)
        await self.db.commit()
        await self.db.refresh(refresh_token)
        return refresh_token

    async def get_by_token(self, token: str) -> Optional[RefreshToken]:
        result = await self.db.execute(select(RefreshToken).where(RefreshToken.token == token))
        return result.scalar_one_or_none()

    async def delete_by_token(self, token: str) -> bool:
        refresh_token = await self.get_by_token(token)
        if refresh_token:
            await self.db.delete(refresh_token)
            await self.db.commit()
            return True
        return False

    async def delete_by_user_id(self, user_id: str) -> bool:
        from sqlalchemy import delete
        result = await self.db.execute(
            delete(RefreshToken).where(RefreshToken.user_id == user_id)
        )
        await self.db.commit()
        return result.rowcount > 0
