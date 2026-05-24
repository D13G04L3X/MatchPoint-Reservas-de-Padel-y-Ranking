from datetime import datetime
from uuid import UUID

from domain.models.enums import BookingStatus
from domain.ports.booking_repository import BookingRepository
from domain.ports.event_publisher import EventPublisher
from domain.services.booking_service import BookingDomainError, BookingDomainService
from application.dtos.booking_response_dto import BookingResponseDTO


class CancelBookingUseCase:
    """Use case for cancelling a booking."""

    def __init__(
        self, booking_repository: BookingRepository, event_publisher: EventPublisher
    ) -> None:
        self._booking_repository = booking_repository
        self._event_publisher = event_publisher

    async def execute(
        self, booking_id: UUID, player_id: UUID, now: datetime
    ) -> BookingResponseDTO:
        """Cancel a booking and return the updated response DTO."""

        booking = await self._booking_repository.get_by_id(booking_id)
        if booking is None:
            raise BookingDomainError("Booking not found.")
        if booking.player_id.value != player_id:
            raise BookingDomainError("Booking does not belong to the player.")

        is_late = BookingDomainService.is_late_cancellation(booking, now)
        status = BookingStatus.CANCELLED_LATE if is_late else BookingStatus.CANCELLED_EARLY

        updated = await self._booking_repository.update_status(booking_id, status)

        if is_late:
            await self._event_publisher.publish_booking_cancelled_late(
                booking_id=booking_id,
                player_id=player_id,
                cancelled_at=now,
                scheduled_at=booking.start_time,
            )

        return BookingResponseDTO.from_entity(updated)

