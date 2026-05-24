from abc import ABC, abstractmethod
from uuid import UUID

from domain.models.membership import Membership


class MembershipRepository(ABC):
    """Port for membership persistence operations."""

    @abstractmethod
    async def get_active_by_player(self, player_id: UUID) -> Membership | None:
        """Return the active membership for a player, if any."""

