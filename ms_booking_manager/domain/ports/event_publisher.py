from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class EventPublisher(ABC):
    """Port for publishing booking-related domain events."""

    @abstractmethod
    async def publish_booking_created(self, booking_id: UUID) -> None:
        """Publish a booking created event."""

    @abstractmethod
    async def publish_booking_cancelled_late(
        self,
        booking_id: UUID,
        player_id: UUID,
        cancelled_at: datetime,
        scheduled_at: datetime,
    ) -> None:
        """Publish a late cancellation event for penalty processing."""

    @abstractmethod
    async def publish_booking_confirmed(self, booking_id: UUID) -> None:
        """Publish a booking confirmation event."""

