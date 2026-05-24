from dataclasses import dataclass
from datetime import datetime
from uuid import UUID

from domain.models.enums import MembershipStatus


@dataclass(frozen=True)
class Player:
    """Player entity.

    Fields:
        id: Unique player identifier.
        username: Public username for the player.
        email: Contact email for the player.
        membership_status: Current membership status for access checks.
        restriction_active: True when the player is restricted.
        restriction_until: Restriction end time, or None if not restricted.
    """

    id: UUID
    username: str
    email: str
    membership_status: MembershipStatus
    restriction_active: bool
    restriction_until: datetime | None

    def __post_init__(self) -> None:
        if not isinstance(self.id, UUID):
            raise TypeError("Player id must be a UUID.")
        if not isinstance(self.username, str) or not self.username.strip():
            raise ValueError("Player username must be a non-empty string.")
        if not isinstance(self.email, str) or "@" not in self.email:
            raise ValueError("Player email must contain '@'.")
        if not isinstance(self.membership_status, MembershipStatus):
            raise TypeError("Player membership_status must be a MembershipStatus.")
        if not isinstance(self.restriction_active, bool):
            raise TypeError("Player restriction_active must be a boolean.")
        if self.restriction_until is not None and not isinstance(self.restriction_until, datetime):
            raise TypeError("Player restriction_until must be datetime or None.")

