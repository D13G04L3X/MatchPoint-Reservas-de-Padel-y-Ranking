from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field

from domain.models.enums import PlanType


class MembershipValidationResponseDTO(BaseModel):
    """Response for membership validation.

    Fields:
        player_id: Player whose membership was validated.
        is_active: True when membership is active.
        plan_type: Plan type for the membership.
        valid_until: Timestamp when membership expires.
        has_restriction: True when the player is restricted.
    """

    player_id: UUID = Field(..., description="Player whose membership was validated.")
    is_active: bool = Field(..., description="True when membership is active.")
    plan_type: PlanType | None = Field(
        None, description="Plan type for the membership."
    )
    valid_until: datetime | None = Field(
        None, description="Timestamp when membership expires."
    )
    has_restriction: bool = Field(
        ..., description="True when the player is restricted."
    )

