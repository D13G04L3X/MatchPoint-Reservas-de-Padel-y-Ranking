from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.models.enums import PlanType


@dataclass(frozen=True)
class Membership:
    """Membership entity.

    Fields:
        id: Unique membership identifier.
        player_id: Player who owns the membership.
        plan_type: Plan type for the membership.
        valid_until: Date when the membership expires.
        is_active: True when membership is currently active.
    """

    id: UUID
    player_id: UUID
    plan_type: PlanType
    valid_until: datetime
    is_active: bool

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise TypeError("Membership id must be a UUID.")
        if not isinstance(self.player_id, UUID):
            raise TypeError("Membership player_id must be a UUID.")
        if not isinstance(self.plan_type, PlanType):
            raise TypeError("Membership plan_type must be a PlanType.")
        if not isinstance(self.valid_until, datetime):
            raise TypeError("Membership valid_until must be a datetime.")
        if not isinstance(self.is_active, bool):
            raise TypeError("Membership is_active must be a boolean.")

