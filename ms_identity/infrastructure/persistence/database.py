import asyncio
import logging

from collections.abc import AsyncIterator

from sqlalchemy.ext.asyncio import AsyncSession, async_sessionmaker, create_async_engine
from sqlalchemy.orm import DeclarativeBase

from config import settings

logger = logging.getLogger(__name__)


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


async def init_db(retries: int = 5, delay: float = 3.0) -> None:
    """Create database tables on startup with retry backoff."""
    from infrastructure.persistence import models  # noqa: F401

    for attempt in range(1, retries + 1):
        try:
            async with engine.begin() as conn:
                await conn.run_sync(Base.metadata.create_all)
            logger.info("Database initialized successfully.")
            return
        except Exception as e:
            if attempt == retries:
                logger.error("Database init failed after %d attempts: %s", retries, e)
                raise
            logger.warning(
                "Database not ready (attempt %d/%d), retrying in %.1fs...",
                attempt, retries, delay,
            )
            await asyncio.sleep(delay)