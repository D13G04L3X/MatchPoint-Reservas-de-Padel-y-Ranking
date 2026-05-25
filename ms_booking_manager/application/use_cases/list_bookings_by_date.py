from datetime import date as Date
from uuid import UUID

from application.dtos.booking_response_dto import BookingResponseDTO
from domain.ports.booking_repository import BookingRepository


class ListBookingsByDateUseCase:
    """Use case for listing bookings on a given date."""

    def __init__(self, booking_repository: BookingRepository) -> None:
        self._booking_repository = booking_repository

    async def execute(
        self,
        date: Date,
        *,
        player_id: UUID | None = None,
        include_cancelled: bool = False,
    ) -> list[BookingResponseDTO]:
        """Return bookings scheduled for the given date."""

        bookings = await self._booking_repository.list_by_date(
            date,
            player_id=player_id,
            include_cancelled=include_cancelled,
        )
        return [BookingResponseDTO.from_entity(booking) for booking in bookings]
