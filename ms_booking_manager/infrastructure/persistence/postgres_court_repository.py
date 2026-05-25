from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.court import Court
from domain.ports.court_repository import CourtRepository
from infrastructure.persistence.models import CourtORM


class PostgresCourtRepository(CourtRepository):
    """PostgreSQL implementation of the court repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, orm: CourtORM) -> Court:
        return Court(
            id=orm.id,
            name=orm.name,
            description=orm.description,
            is_active=orm.is_active,
        )

    async def list_active(self) -> list[Court]:
        result = await self._session.execute(
            select(CourtORM)
            .where(CourtORM.is_active.is_(True))
            .order_by(CourtORM.name)
        )
        return [self._to_domain(orm) for orm in result.scalars().all()]

    async def get_by_id(self, court_id: UUID) -> Court | None:
        result = await self._session.execute(
            select(CourtORM).where(CourtORM.id == court_id)
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None
