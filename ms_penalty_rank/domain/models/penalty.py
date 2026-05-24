from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.models.enums import PenaltyReason


@dataclass(frozen=True)
class Penalty:
    """Penalty entity.

    Fields:
        id: Unique penalty identifier.
        player_id: Player who receives the penalty.
        reason: Reason for the penalty.
        applied_at: Timestamp when the penalty was applied.
        expires_at: Timestamp when the penalty expires.
        is_active: True when the penalty is currently active.
    """

    id: UUID
    player_id: UUID
    reason: PenaltyReason
    applied_at: datetime
    expires_at: datetime
    is_active: bool

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise TypeError("Penalty id must be a UUID.")
        if not isinstance(self.player_id, UUID):
            raise TypeError("Penalty player_id must be a UUID.")
        if not isinstance(self.reason, PenaltyReason):
            raise TypeError("Penalty reason must be a PenaltyReason.")
        if not isinstance(self.applied_at, datetime):
            raise TypeError("Penalty applied_at must be a datetime.")
        if not isinstance(self.expires_at, datetime):
            raise TypeError("Penalty expires_at must be a datetime.")
        if self.applied_at > self.expires_at:
            raise ValueError("Penalty applied_at must be before expires_at.")
        if not isinstance(self.is_active, bool):
            raise TypeError("Penalty is_active must be a boolean.")

