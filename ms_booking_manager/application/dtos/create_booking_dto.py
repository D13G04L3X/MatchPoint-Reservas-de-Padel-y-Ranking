from datetime import datetime, timedelta, timezone
from uuid import UUID

from pydantic import BaseModel, Field, model_validator


class CreateBookingDTO(BaseModel):
    """Input data for creating a booking.

    Fields:
        court_id: Court where the booking will occur.
        player_id: Organizer who owns the booking.
        team_local_ids: Local team players (2) including the organizer.
        team_visit_ids: Visiting team players (2) for ranked bookings.
        start_time: Scheduled start time.
        end_time: Scheduled end time.
        is_ranked: True when the booking is ranked.
    """

    court_id: UUID = Field(..., description="Court where the booking will occur.")
    player_id: UUID = Field(..., description="Organizer who owns the booking.")
    team_local_ids: list[UUID] = Field(
        ..., description="Local team player ids (2) including organizer."
    )
    team_visit_ids: list[UUID] | None = Field(
        default=None, description="Visiting team player ids (2) for ranked bookings."
    )
    start_time: datetime = Field(..., description="Scheduled start time.")
    end_time: datetime = Field(..., description="Scheduled end time.")
    is_ranked: bool = Field(False, description="True when the booking is ranked.")

    @model_validator(mode="after")
    def validate_time_window(self) -> "CreateBookingDTO":
        """Validate that the booking duration is within allowed limits."""

        now = datetime.now(timezone.utc)
        if self.start_time <= now:
            raise ValueError("start_time must be in the future.")
        if self.end_time <= self.start_time:
            raise ValueError("end_time must be after start_time.")
        if self.end_time - self.start_time > timedelta(hours=2):
            raise ValueError("Booking duration must be at most 2 hours.")
        return self

    @model_validator(mode="after")
    def validate_teams(self) -> "CreateBookingDTO":
        """Validate team composition rules."""

        local_ids = list(self.team_local_ids or [])
        if len(local_ids) != 2:
            raise ValueError("Local team must have exactly 2 players.")
        if self.player_id not in local_ids:
            raise ValueError("Organizer must be in local team.")
        if len(set(local_ids)) != len(local_ids):
            raise ValueError("Local team has duplicate players.")

        if self.is_ranked:
            if self.team_visit_ids is None:
                raise ValueError("Ranked bookings require a visiting team.")
            visit_ids = list(self.team_visit_ids)
            if len(visit_ids) != 2:
                raise ValueError("Visiting team must have exactly 2 players.")
            if len(set(visit_ids)) != len(visit_ids):
                raise ValueError("Visiting team has duplicate players.")
            if set(local_ids) & set(visit_ids):
                raise ValueError("Players cannot be in both teams.")
        elif self.team_visit_ids is not None:
            raise ValueError("Casual bookings must not include a visiting team.")

        return self

