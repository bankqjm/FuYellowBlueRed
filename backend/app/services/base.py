from sqlalchemy.ext.asyncio import AsyncSession
from typing import Optional

__all__ = ["BaseService"]


class BaseService:
    def __init__(self, db: AsyncSession):
        self.db = db

    async def commit(self):
        await self.db.commit()

    async def refresh(self, obj):
        await self.db.refresh(obj)

    async def flush(self):
        await self.db.flush()
