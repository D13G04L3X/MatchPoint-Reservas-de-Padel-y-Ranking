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
        player_id: Primary player who owns the booking.
        guest_player_ids: Guest players included in the booking.
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
    guest_player_ids: list[PlayerId]
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
        if not isinstance(self.guest_player_ids, list):
            raise TypeError("Booking guest_player_ids must be a list.")
        if not all(isinstance(player_id, PlayerId) for player_id in self.guest_player_ids):
            raise TypeError("Booking guest_player_ids must contain PlayerId values.")

        TimeSlot(self.start_time, self.end_time)

    @property
    def is_premium(self) -> bool:
        """Derived premium flag based on the booking time slot."""

        return TimeSlot(self.start_time, self.end_time).is_premium()

