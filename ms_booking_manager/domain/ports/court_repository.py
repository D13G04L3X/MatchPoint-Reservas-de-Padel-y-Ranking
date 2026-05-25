from abc import ABC, abstractmethod
from uuid import UUID

from domain.models.court import Court


class CourtRepository(ABC):
    """Port for court persistence operations."""

    @abstractmethod
    async def list_active(self) -> list[Court]:
        """Return all courts that can be booked."""

    @abstractmethod
    async def get_by_id(self, court_id: UUID) -> Court | None:
        """Return a court by id, if it exists."""
