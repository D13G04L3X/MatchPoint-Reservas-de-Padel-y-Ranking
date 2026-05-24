from datetime import datetime, timedelta
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class CreateBookingDTO(BaseModel):
    """Input data for creating a booking.

    Fields:
        court_id: Court where the booking will occur.
        player_id: Player who owns the booking.
        guest_player_ids: Guest players included in the booking (max 3).
        start_time: Scheduled start time.
        end_time: Scheduled end time.
        is_ranked: True when the booking is ranked.
    """

    court_id: UUID = Field(..., description="Court where the booking will occur.")
    player_id: UUID = Field(..., description="Player who owns the booking.")
    guest_player_ids: list[UUID] = Field(
        default_factory=list,
        max_length=3,
        description="Guest players included in the booking (max 3).",
    )
    start_time: datetime = Field(..., description="Scheduled start time.")
    end_time: datetime = Field(..., description="Scheduled end time.")
    is_ranked: bool = Field(False, description="True when the booking is ranked.")

    @model_validator(mode="after")
    def validate_time_window(self) -> "CreateBookingDTO":
        """Validate that the booking duration is within allowed limits."""

        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time.")
        if self.end_time - self.start_time > timedelta(hours=2):
            raise ValueError("Booking duration must be at most 2 hours.")
        return self

