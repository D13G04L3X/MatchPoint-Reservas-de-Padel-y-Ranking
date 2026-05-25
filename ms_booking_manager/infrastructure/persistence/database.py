from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings


class Base(DeclarativeBase):
    """Base class for SQLAlchemy ORM models."""


engine = create_async_engine(settings.DATABASE_URL, echo=False)
AsyncSessionLocal = async_sessionmaker(
    engine, class_=AsyncSession, expire_on_commit=False
)


async def get_db() -> AsyncIterator[AsyncSession]:
    """Yield an async database session for request-scoped usage."""

    async with AsyncSessionLocal() as session:
        yield session


async def init_db() -> None:
    """Create database tables on startup."""

    from infrastructure.persistence import models  # noqa: F401
    from infrastructure.persistence.seed_courts import seed_default_courts

    async with engine.begin() as conn:
        await conn.run_sync(Base.metadata.create_all)

    async with AsyncSessionLocal() as session:
        await seed_default_courts(session)

