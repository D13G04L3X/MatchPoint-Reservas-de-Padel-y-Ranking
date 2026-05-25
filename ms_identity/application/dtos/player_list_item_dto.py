from datetime import datetime
from uuid import UUID

from pydantic import BaseModel

from domain.models.enums import MembershipStatus


class PlayerListItemDTO(BaseModel):
    """Public player representation for debugging and admin reads."""

    id: UUID
    username: str
    email: str
    membership_status: MembershipStatus
    restriction_active: bool
    restriction_until: datetime | None
