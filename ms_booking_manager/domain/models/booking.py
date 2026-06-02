from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.models.enums import BookingStatus
from domain.models.value_objects import PlayerId, TimeSlot


@dataclass(frozen=True)
class Booking:
    """Booking entity.

    Fields:
        id: Unique booking identifier.
        court_id: Court where the booking occurs.
        player_id: Organizer who owns the booking.
        team_local_ids: Local team players (2). Must include the organizer.
        team_visit_ids: Visiting team players (2) for ranked matches.
        start_time: Scheduled start time.
        end_time: Scheduled end time.
        status: Lifecycle status of the booking.
        is_premium: Derived flag for premium hours (18-22).
        is_ranked: True when the booking is ranked.
        created_at: Timestamp when the booking was created.
    """

    id: UUID
    court_id: UUID
    player_id: PlayerId
    team_local_ids: list[PlayerId]
    team_visit_ids: list[PlayerId] | None
    start_time: datetime
    end_time: datetime
    status: BookingStatus
    is_ranked: bool
    created_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise TypeError("Booking id must be a UUID.")
        if not isinstance(self.court_id, UUID):
            raise TypeError("Booking court_id must be a UUID.")
        if not isinstance(self.player_id, PlayerId):
            raise TypeError("Booking player_id must be a PlayerId.")
        if not isinstance(self.team_local_ids, list):
            raise TypeError("Booking team_local_ids must be a list.")
        if not all(isinstance(player_id, PlayerId) for player_id in self.team_local_ids):
            raise TypeError("Booking team_local_ids must contain PlayerId values.")
        if len(self.team_local_ids) != 2:
            raise ValueError("Booking team_local_ids must have 2 players.")
        if self.player_id not in self.team_local_ids:
            raise ValueError("Booking player_id must be in team_local_ids.")
        if len({player_id.value for player_id in self.team_local_ids}) != len(
            self.team_local_ids
        ):
            raise ValueError("Booking team_local_ids must be unique.")

        if self.team_visit_ids is None:
            if self.is_ranked:
                raise ValueError("Ranked bookings require team_visit_ids.")
        else:
            if not isinstance(self.team_visit_ids, list):
                raise TypeError("Booking team_visit_ids must be a list.")
            if not all(
                isinstance(player_id, PlayerId) for player_id in self.team_visit_ids
            ):
                raise TypeError("Booking team_visit_ids must contain PlayerId values.")
            if len(self.team_visit_ids) != 2:
                raise ValueError("Booking team_visit_ids must have 2 players.")
            if len({player_id.value for player_id in self.team_visit_ids}) != len(
                self.team_visit_ids
            ):
                raise ValueError("Booking team_visit_ids must be unique.")
            if {
                player_id.value for player_id in self.team_local_ids
            } & {player_id.value for player_id in self.team_visit_ids}:
                raise ValueError("Booking team players must be unique across teams.")
            if not self.is_ranked:
                raise ValueError("Casual bookings must not include team_visit_ids.")

        TimeSlot(self.start_time, self.end_time)

    @property
    def is_premium(self) -> bool:
        """Derived premium flag based on the booking time slot."""

        return TimeSlot(self.start_time, self.end_time).is_premium()

