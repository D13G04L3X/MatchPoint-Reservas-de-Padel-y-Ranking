from enum import Enum


class BookingStatus(str, Enum):
    """Status of a booking in its lifecycle.

    Fields:
        PENDING: Reservation requested but not confirmed.
        CONFIRMED: Reservation accepted and active.
        CANCELLED_EARLY: Cancelled with sufficient notice.
        CANCELLED_LATE: Cancelled too close to the start time.
    """

    PENDING = "PENDING"
    CONFIRMED = "CONFIRMED"
    CANCELLED_EARLY = "CANCELLED_EARLY"
    CANCELLED_LATE = "CANCELLED_LATE"

