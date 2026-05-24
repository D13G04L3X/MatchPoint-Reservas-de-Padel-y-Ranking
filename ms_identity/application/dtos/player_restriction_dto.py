from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field


class PlayerRestrictionDTO(BaseModel):
    """Restriction status for a player.

    Fields:
        player_id: Player whose restriction is reported.
        restriction_active: True when the restriction is active.
        restriction_until: Timestamp when restriction ends, or None.
    """

    player_id: UUID = Field(..., description="Player whose restriction is reported.")
    restriction_active: bool = Field(
        ..., description="True when the restriction is active."
    )
    restriction_until: datetime | None = Field(
        None, description="Timestamp when restriction ends, or None."
    )

