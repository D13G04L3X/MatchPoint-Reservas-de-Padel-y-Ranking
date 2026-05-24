from abc import ABC, abstractmethod
from uuid import UUID

from domain.models.penalty import Penalty


class PenaltyRepository(ABC):
    """Port for penalty persistence operations."""

    @abstractmethod
    async def create(self, penalty: Penalty) -> Penalty:
        """Persist a penalty and return the stored entity."""

    @abstractmethod
    async def get_active_by_player(self, player_id: UUID) -> list[Penalty]:
        """Return active penalties for the given player id."""

