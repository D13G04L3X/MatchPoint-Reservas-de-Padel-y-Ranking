from uuid import UUID

from sqlalchemy.ext.asyncio import AsyncSession

from infrastructure.persistence.models import CourtORM

DEFAULT_COURTS: tuple[tuple[UUID, str, str], ...] = (
    (
        UUID("a1a1a1a1-a1a1-4111-a111-000000000001"),
        "Cancha 1",
        "Cristal cubierta",
    ),
    (
        UUID("a1a1a1a1-a1a1-4111-a111-000000000002"),
        "Cancha 2",
        "Cristal exterior",
    ),
    (
        UUID("a1a1a1a1-a1a1-4111-a111-000000000003"),
        "Cancha 3",
        "Panorámica",
    ),
)


async def seed_default_courts(session: AsyncSession) -> None:
    """Insert default courts when they are missing."""

    for court_id, name, description in DEFAULT_COURTS:
        existing = await session.get(CourtORM, court_id)
        if existing is not None:
            continue
        session.add(
            CourtORM(
                id=court_id,
                name=name,
                description=description,
                is_active=True,
            )
        )

    await session.commit()
