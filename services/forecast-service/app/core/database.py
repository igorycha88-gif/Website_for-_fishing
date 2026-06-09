from sqlalchemy.ext.asyncio import create_async_engine, AsyncSession, async_sessionmaker
from sqlalchemy.orm import DeclarativeBase
from redis.asyncio import Redis


class Base(DeclarativeBase):
    pass


class Database:
    def __init__(self, database_url: str):
        self.engine = create_async_engine(database_url, echo=True)
        self.async_session = async_sessionmaker(
            self.engine, class_=AsyncSession, expire_on_commit=False
        )

    async def get_session(self):
        async with self.async_session() as session:
            yield session

    async def close(self):
        await self.engine.dispose()


from app.core.config import settings

database = Database(settings.DATABASE_URL)
redis_client = Redis.from_url(settings.REDIS_URL, decode_responses=False)


async def get_db():
    async for session in database.get_session():
        yield session


async def get_redis():
    yield redis_client
