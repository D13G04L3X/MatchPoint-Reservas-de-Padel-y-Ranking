from datetime import datetime, timezone
from uuid import uuid4

from domain.models.booking import Booking
from domain.models.enums import BookingStatus
from domain.models.value_objects import PlayerId, TimeSlot
from domain.ports.booking_repository import BookingRepository
from domain.ports.event_publisher import EventPublisher
from domain.ports.identity_client import IdentityClient
from domain.ports.ranking_client import RankingClient
from domain.services.booking_service import BookingDomainService, BookingOverlapError
from application.dtos.booking_response_dto import BookingResponseDTO
from application.dtos.create_booking_dto import CreateBookingDTO


class CreateBookingUseCase:
    """Use case for creating a booking with domain rule checks."""

    def __init__(
        self,
        booking_repository: BookingRepository,
        identity_client: IdentityClient,
        ranking_client: RankingClient,
        event_publisher: EventPublisher,
    ) -> None:
        self._booking_repository = booking_repository
        self._identity_client = identity_client
        self._ranking_client = ranking_client
        self._event_publisher = event_publisher

    async def execute(self, dto: CreateBookingDTO) -> BookingResponseDTO:
        """Create a booking and return the response DTO."""

        slot = TimeSlot(start_time=dto.start_time, end_time=dto.end_time)
        if slot.is_premium():
            has_membership = await self._identity_client.validate_membership(dto.player_id)
            has_restriction = await self._identity_client.get_player_restriction(dto.player_id)
            BookingDomainService.validate_premium_slot(
                slot, has_membership, has_restriction
            )

        if dto.is_ranked:
            player_ids = [dto.player_id] + list(dto.guest_player_ids)
            levels = await self._ranking_client.get_players_levels(player_ids)
            BookingDomainService.validate_ranked_levels(levels)

        if await self._booking_repository.exists_overlap(dto.court_id, slot):
            raise BookingOverlapError("Booking overlaps with an existing reservation.")

        created_at = datetime.now(timezone.utc)
        booking = Booking(
            id=uuid4(),
            court_id=dto.court_id,
            player_id=PlayerId(dto.player_id),
            guest_player_ids=[PlayerId(player_id) for player_id in dto.guest_player_ids],
            start_time=dto.start_time,
            end_time=dto.end_time,
            status=BookingStatus.PENDING,
            is_ranked=dto.is_ranked,
            created_at=created_at,
        )

        created = await self._booking_repository.create(booking)
        await self._event_publisher.publish_booking_created(created.id)

        return BookingResponseDTO.from_entity(created)

