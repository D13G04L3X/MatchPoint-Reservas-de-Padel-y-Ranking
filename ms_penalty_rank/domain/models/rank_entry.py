from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class RankEntry:
    """Rank entry for a player.

    Fields:
        player_id: Player whose ranking is tracked.
        level: Skill level from 0.0 to 10.0.
        wins: Total wins recorded.
        losses: Total losses recorded.
        updated_at: Timestamp of the last update.
    """

    player_id: UUID
    level: float
    wins: int
    losses: int
    updated_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.player_id, UUID):
            raise TypeError("RankEntry player_id must be a UUID.")
        if not isinstance(self.level, (int, float)):
            raise TypeError("RankEntry level must be a number.")
        if not 0.0 <= float(self.level) <= 10.0:
            raise ValueError("RankEntry level must be between 0.0 and 10.0.")
        if not isinstance(self.wins, int) or self.wins < 0:
            raise ValueError("RankEntry wins must be a non-negative int.")
        if not isinstance(self.losses, int) or self.losses < 0:
            raise ValueError("RankEntry losses must be a non-negative int.")
        if not isinstance(self.updated_at, datetime):
            raise TypeError("RankEntry updated_at must be a datetime.")

