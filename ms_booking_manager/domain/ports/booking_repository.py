from abc import ABC, abstractmethod
from datetime import date as Date
from uuid import UUID

from domain.models.booking import Booking
from domain.models.enums import BookingStatus
from domain.models.value_objects import TimeSlot


class BookingRepository(ABC):
    """Port for booking persistence operations."""

    @abstractmethod
    async def create(self, booking: Booking) -> Booking:
        """Persist a new booking and return the stored entity."""

    @abstractmethod
    async def get_by_id(self, booking_id: UUID) -> Booking | None:
        """Return a booking by its id, or None if not found."""

    @abstractmethod
    async def get_by_player(self, player_id: UUID) -> list[Booking]:
        """Return all bookings for the given player id."""

    @abstractmethod
    async def list_by_date(
        self,
        date: Date,
        *,
        player_id: UUID | None = None,
        include_cancelled: bool = False,
    ) -> list[Booking]:
        """Return bookings that start on the given date (club local time)."""

    @abstractmethod
    async def update_status(self, booking_id: UUID, status: BookingStatus) -> Booking:
        """Update booking status and return the updated entity."""

    @abstractmethod
    async def exists_overlap(self, court_id: UUID, slot: TimeSlot) -> bool:
        """Return True if another booking overlaps the given slot."""

