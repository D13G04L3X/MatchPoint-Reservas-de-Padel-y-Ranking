from abc import ABC, abstractmethod
from uuid import UUID

from domain.models.rank_entry import RankEntry


class RankRepository(ABC):
    """Port for rank persistence operations."""

    @abstractmethod
    async def get_by_player(self, player_id: UUID) -> RankEntry | None:
        """Return the rank entry for a player, or None if missing."""

    @abstractmethod
    async def update_level(self, player_id: UUID, level: float) -> RankEntry:
        """Update the player level and return the updated rank entry."""

    @abstractmethod
    async def list_ranked(self) -> list[RankEntry]:
        """Return all ranked entries for listing or leaderboards."""

