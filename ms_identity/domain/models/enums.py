from enum import Enum


class MembershipStatus(str, Enum):
    """Current membership state for a player.

    Fields:
        ACTIVE: Membership is valid and usable.
        EXPIRED: Membership has passed its validity period.
        SUSPENDED: Membership is temporarily suspended.
    """

    ACTIVE = "ACTIVE"
    EXPIRED = "EXPIRED"
    SUSPENDED = "SUSPENDED"


class PlanType(str, Enum):
    """Plan type for a membership.

    Fields:
        BASIC: Basic plan without premium perks.
        PREMIUM: Premium plan with enhanced access.
    """

    BASIC = "BASIC"
    PREMIUM = "PREMIUM"

