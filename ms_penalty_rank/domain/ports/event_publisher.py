from abc import ABC, abstractmethod
from datetime import datetime
from uuid import UUID


class EventPublisher(ABC):
    """Port for publishing penalty and restriction events."""

    @abstractmethod
    async def publish_user_restricted(self, player_id: UUID, restricted_until: datetime) -> None:
        """Publish a user restriction event for MS-Identity."""

