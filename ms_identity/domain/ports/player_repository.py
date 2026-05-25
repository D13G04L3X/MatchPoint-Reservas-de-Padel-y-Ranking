from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID

from domain.models.membership import Membership
from domain.models.player import Player


class PlayerRepository(ABC):
    """Port for player persistence operations."""

    @abstractmethod
    async def get_by_id(self, player_id: UUID) -> Player | None:
        """Return a player by id, or None if not found."""

    @abstractmethod
    async def list_all(self) -> list[Player]:
        """Return all players stored in the repository."""

    @abstractmethod
    async def update_restriction(
        self, player_id: UUID, restriction_active: bool, restriction_until: datetime | None
    ) -> Player:
        """Update restriction flags and return the updated player."""

    @abstractmethod
    async def get_membership(self, player_id: UUID) -> Membership | None:
        """Return the membership record for a player, if any."""

