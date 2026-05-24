from enum import Enum


class PenaltyReason(str, Enum):
    """Reason for a penalty.

    Fields:
        LATE_CANCELLATION: Cancelled too close to the start time.
        NO_SHOW: Player did not show up for the booking.
    """

    LATE_CANCELLATION = "LATE_CANCELLATION"
    NO_SHOW = "NO_SHOW"

