from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.booking import Booking
from domain.models.enums import BookingStatus
from domain.models.value_objects import PlayerId, TimeSlot
from domain.ports.booking_repository import BookingRepository
from infrastructure.persistence.models import BookingORM


class PostgresBookingRepository(BookingRepository):
    """PostgreSQL implementation of the booking repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, orm: BookingORM) -> Booking:
        return Booking(
            id=orm.id,
            court_id=orm.court_id,
            player_id=PlayerId(orm.player_id),
            guest_player_ids=[PlayerId(value) for value in orm.guest_player_ids],
            start_time=orm.start_time,
            end_time=orm.end_time,
            status=orm.status,
            is_ranked=orm.is_ranked,
            created_at=orm.created_at,
        )

    def _to_orm(self, booking: Booking) -> BookingORM:
        return BookingORM(
            id=booking.id,
            court_id=booking.court_id,
            player_id=booking.player_id.value,
            guest_player_ids=[guest.value for guest in booking.guest_player_ids],
            start_time=booking.start_time,
            end_time=booking.end_time,
            status=booking.status,
            is_ranked=booking.is_ranked,
            created_at=booking.created_at,
        )

    async def create(self, booking: Booking) -> Booking:
        orm = self._to_orm(booking)
        self._session.add(orm)
        await self._session.commit()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    async def get_by_id(self, booking_id: UUID) -> Booking | None:
        result = await self._session.execute(
            select(BookingORM).where(BookingORM.id == booking_id)
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def get_by_player(self, player_id: UUID) -> list[Booking]:
        result = await self._session.execute(
            select(BookingORM).where(BookingORM.player_id == player_id)
        )
        return [self._to_domain(orm) for orm in result.scalars().all()]

    async def update_status(self, booking_id: UUID, status: BookingStatus) -> Booking:
        result = await self._session.execute(
            select(BookingORM).where(BookingORM.id == booking_id)
        )
        orm = result.scalar_one_or_none()
        if orm is None:
            raise ValueError("Booking not found.")
        orm.status = status
        await self._session.commit()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    async def exists_overlap(self, court_id: UUID, slot: TimeSlot) -> bool:
        stmt = (
            select(BookingORM.id)
            .where(
                BookingORM.court_id == court_id,
                ~BookingORM.status.in_(
                    [BookingStatus.CANCELLED_EARLY, BookingStatus.CANCELLED_LATE]
                ),
                BookingORM.start_time < slot.end_time,
                BookingORM.end_time > slot.start_time,
            )
            .limit(1)
        )
        result = await self._session.execute(stmt)
        return result.scalar_one_or_none() is not None

