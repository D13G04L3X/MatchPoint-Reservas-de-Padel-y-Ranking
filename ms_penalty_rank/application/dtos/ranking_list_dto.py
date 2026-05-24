from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PlayerLevelEntry(BaseModel):
    """Ranking list entry for a player.

    Fields:
        player_id: Player whose ranking is listed.
        level: Skill level from 0.0 to 10.0.
        wins: Total wins recorded.
        losses: Total losses recorded.
    """

    player_id: UUID = Field(..., description="Player whose ranking is listed.")
    level: float = Field(..., ge=0.0, le=10.0, description="Skill level (0.0-10.0).")
    wins: int = Field(..., ge=0, description="Total wins recorded.")
    losses: int = Field(..., ge=0, description="Total losses recorded.")


class RankingListDTO(BaseModel):
    """Ranking list response.

    Fields:
        entries: List of ranking entries.
        generated_at: Timestamp when the list was generated.
    """

    entries: list[PlayerLevelEntry] = Field(
        default_factory=list, description="List of ranking entries."
    )
    generated_at: datetime = Field(
        ..., description="Timestamp when the list was generated."
    )

