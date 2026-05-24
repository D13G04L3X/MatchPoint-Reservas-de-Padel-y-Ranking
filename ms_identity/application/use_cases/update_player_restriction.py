from datetime import datetime
from uuid import UUID

from domain.ports.player_repository import PlayerRepository


class UpdatePlayerRestrictionUseCase:
    """Use case for updating player restriction state."""

    def __init__(self, player_repository: PlayerRepository) -> None:
        self._player_repository = player_repository

    async def execute(self, player_id: UUID, restriction_until: datetime) -> None:
        """Update player restriction flags."""
        player = await self._player_repository.get_by_id(player_id)
        if player is None:
            raise ValueError("Player not found.")

        await self._player_repository.update_restriction(
            player_id=player_id,
            restriction_active=True,
            restriction_until=restriction_until,
        )

