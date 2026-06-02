from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from domain.models.booking import Booking
from domain.models.enums import BookingStatus


class BookingResponseDTO(BaseModel):
    """Output data for returning booking details.

    Fields:
        id: Unique identifier for the booking.
        court_id: Court where the booking occurs.
        player_id: Organizer who owns the booking.
        team_local_ids: Local team players (2) including organizer.
        team_visit_ids: Visiting team players (2) for ranked bookings.
        status: Current booking status.
        is_premium: True when the booking starts in premium hours.
        is_ranked: True when the booking is ranked.
        start_time: Scheduled start time.
        end_time: Scheduled end time.
        created_at: Timestamp when the booking was created.
    """

    id: UUID = Field(..., description="Unique identifier for the booking.")
    court_id: UUID = Field(..., description="Court where the booking occurs.")
    player_id: UUID = Field(..., description="Organizer who owns the booking.")
    team_local_ids: list[UUID] = Field(
        ..., description="Local team player ids (2) including organizer."
    )
    team_visit_ids: list[UUID] | None = Field(
        default=None, description="Visiting team player ids (2) for ranked bookings."
    )
    status: BookingStatus = Field(..., description="Current booking status.")
    is_premium: bool = Field(..., description="True when booking is in premium hours.")
    is_ranked: bool = Field(..., description="True when the booking is ranked.")
    start_time: datetime = Field(..., description="Scheduled start time.")
    end_time: datetime = Field(..., description="Scheduled end time.")
    created_at: datetime = Field(..., description="Timestamp when the booking was created.")

    @classmethod
    def from_entity(cls, booking: Booking) -> "BookingResponseDTO":
        """Create a response DTO from a booking entity."""

        return cls(
            id=booking.id,
            court_id=booking.court_id,
            player_id=booking.player_id.value,
            team_local_ids=[player_id.value for player_id in booking.team_local_ids],
            team_visit_ids=(
                [player_id.value for player_id in booking.team_visit_ids]
                if booking.team_visit_ids is not None
                else None
            ),
            status=booking.status,
            is_premium=booking.is_premium,
            is_ranked=booking.is_ranked,
            start_time=booking.start_time,
            end_time=booking.end_time,
            created_at=booking.created_at,
        )

