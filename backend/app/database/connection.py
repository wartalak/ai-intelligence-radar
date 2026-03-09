"""
Async SQLAlchemy engine and session factory.
"""

from contextlib import asynccontextmanager
from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from app.config import get_settings

settings = get_settings()


def _fix_db_url(url: str) -> str:
    """Convert Render's postgres:// to postgresql+asyncpg:// for asyncpg."""
    if url.startswith("postgres://"):
        url = url.replace("postgres://", "postgresql+asyncpg://", 1)
    elif url.startswith("postgresql://") and "+asyncpg" not in url:
        url = url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return url


_db_url = _fix_db_url(settings.DATABASE_URL)

engine = create_async_engine(
    _db_url,
    echo=settings.ENVIRONMENT == "development",
    pool_size=20,
    max_overflow=10,
    pool_pre_ping=True,
)

async_session_factory = async_sessionmaker(
    engine,
    class_=AsyncSession,
    expire_on_commit=False,
)


@asynccontextmanager
async def create_fresh_session():
    """Create a fresh engine + session for use in Celery tasks.
    
    Each Celery task runs in a new event loop, so we must create
    a fresh engine (not reuse the global one which is bound to
    the import-time loop).
    """
    fresh_engine = create_async_engine(
        _db_url,
        echo=False,
        pool_size=5,
        max_overflow=5,
        pool_pre_ping=True,
    )
    factory = async_sessionmaker(
        fresh_engine,
        class_=AsyncSession,
        expire_on_commit=False,
    )
    async with factory() as session:
        try:
            yield session
        finally:
            await session.close()
    await fresh_engine.dispose()


async def get_db() -> AsyncSession:
    """FastAPI dependency that yields an async database session."""
    async with async_session_factory() as session:
        try:
            yield session
            await session.commit()
        except Exception:
            await session.rollback()
            raise
        finally:
            await session.close()

