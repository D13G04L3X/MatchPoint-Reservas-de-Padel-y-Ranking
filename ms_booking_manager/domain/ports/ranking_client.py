from abc import ABC, abstractmethod
from uuid import UUID


class RankingClient(ABC):
    """Port for ranking queries in MS-PenaltyRank."""

    @abstractmethod
    async def get_player_level(self, player_id: UUID) -> float:
        """Return the current ranking level for a player."""

    @abstractmethod
    async def get_players_levels(self, player_ids: list[UUID]) -> dict[UUID, float]:
        """Return a mapping of player ids to their ranking levels."""

