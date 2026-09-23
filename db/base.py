from sqlalchemy.ext.asyncio import create_async_engine, async_sessionmaker, AsyncSession
from sqlalchemy.orm import DeclarativeBase
from typing import AsyncGenerator
from config import settings

# Async engine yaratish
engine = create_async_engine(
    settings.DATABASE_URL,
    echo=False,
    future=True
)

# Async session factory
AsyncSessionLocal = async_sessionmaker(
    bind=engine,
    class_=AsyncSession,
    expire_on_commit=False,
    autoflush=False
)


class Base(DeclarativeBase):
    """Barcha modellar uchun asosiy klass"""
    pass


async def get_session() -> AsyncGenerator[AsyncSession, None]:
    """Ma'lumotlar bazasi sessiyasini olish uchun generator"""
    async with AsyncSessionLocal() as session:
        try:
            yield session
        finally:
            await session.close()


async def init_db() -> None:
    """Barcha jadvallarni ma'lumotlar bazasida yaratish"""
    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)
