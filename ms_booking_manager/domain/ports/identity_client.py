from abc import ABC, abstractmethod
from uuid import UUID


class IdentityClient(ABC):
    """Port for membership and restriction checks in MS-Identity."""

    @abstractmethod
    async def validate_membership(self, player_id: UUID) -> bool:
        """Return True when the player has an active membership."""

    @abstractmethod
    async def get_player_restriction(self, player_id: UUID) -> bool:
        """Return True when the player is currently restricted."""

