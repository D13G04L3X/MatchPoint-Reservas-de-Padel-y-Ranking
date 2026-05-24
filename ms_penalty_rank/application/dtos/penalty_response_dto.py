from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from domain.models.enums import PenaltyReason


class PenaltyResponseDTO(BaseModel):
    """Penalty response data.

    Fields:
        player_id: Player who receives the penalty.
        reason: Reason for the penalty.
        applied_at: Timestamp when the penalty was applied.
        expires_at: Timestamp when the penalty expires.
        is_active: True when the penalty is currently active.
    """

    player_id: UUID = Field(..., description="Player who receives the penalty.")
    reason: PenaltyReason = Field(..., description="Reason for the penalty.")
    applied_at: datetime = Field(..., description="Timestamp when the penalty was applied.")
    expires_at: datetime = Field(..., description="Timestamp when the penalty expires.")
    is_active: bool = Field(..., description="True when the penalty is currently active.")

