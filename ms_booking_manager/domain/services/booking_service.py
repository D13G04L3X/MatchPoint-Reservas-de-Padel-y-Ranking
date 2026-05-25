from datetime import datetime
from uuid import UUID

from domain.models.booking import Booking
from domain.models.value_objects import TimeSlot


class BookingDomainError(Exception):
    """Base exception for booking domain rule violations."""


class PremiumMembershipRequired(BookingDomainError):
    """Raised when a premium slot requires an active membership."""


class PremiumRestricted(BookingDomainError):
    """Raised when a penalized player attempts a premium slot."""


class RankedLevelDifferenceTooHigh(BookingDomainError):
    """Raised when ranked players have a level gap greater than allowed."""


class BookingOverlapError(BookingDomainError):
    """Raised when a booking overlaps with an existing reservation."""


class CourtNotFoundError(BookingDomainError):
    """Raised when the requested court does not exist or is inactive."""


class BookingDomainService:
    """Pure domain rules for booking validation and decisions."""

    @staticmethod
    def validate_premium_slot(
        slot: TimeSlot, has_membership: bool, has_restriction: bool = False
    ) -> None:
        """Validate membership and restrictions for premium slots."""
        if not slot.is_premium():
            return
        if has_restriction:
            raise PremiumRestricted(
                "Player is restricted from premium slots due to low reliability penalty."
            )
        if not has_membership:
            raise PremiumMembershipRequired("Premium slot requires active membership.")

    @staticmethod
    def validate_ranked_levels(levels: dict[UUID, float]) -> None:
        """Validate that ranked player levels are within the allowed gap."""
        if not levels:
            return
        max_level = max(levels.values())
        min_level = min(levels.values())
        if max_level - min_level > 2.0:
            raise RankedLevelDifferenceTooHigh(
                "Ranked player level difference exceeds 2.0."
            )

    @staticmethod                                              # ← dentro de la clase
    def is_late_cancellation(booking: Booking, now: datetime) -> bool:
        """Return True when the cancellation is within two hours of start."""
        delta = (booking.start_time - now).total_seconds()
        return 0 <= delta < 2 * 60 * 60
