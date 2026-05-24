from uuid import UUID

from pydantic import BaseModel, Field


class PlayerLevelDTO(BaseModel):
    """Rank level data for a player.

    Fields:
        player_id: Player whose ranking is returned.
        level: Skill level from 0.0 to 10.0.
        wins: Total wins recorded.
        losses: Total losses recorded.
    """

    player_id: UUID = Field(..., description="Player whose ranking is returned.")
    level: float = Field(..., ge=0.0, le=10.0, description="Skill level (0.0-10.0).")
    wins: int = Field(..., ge=0, description="Total wins recorded.")
    losses: int = Field(..., ge=0, description="Total losses recorded.")

