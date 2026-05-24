from uuid import UUID

from application.dtos.player_level_dto import PlayerLevelDTO
from domain.ports.rank_repository import RankRepository


class GetPlayerLevelUseCase:
    """Use case for retrieving or creating a player rank entry."""

    def __init__(self, rank_repository: RankRepository) -> None:
        self._rank_repository = rank_repository

    async def execute(self, player_id: UUID) -> PlayerLevelDTO:
        """Return a player's level, creating a default entry if missing."""

        entry = await self._rank_repository.get_by_player(player_id)
        if entry is None:
            entry = await self._rank_repository.update_level(player_id, 5.0)
        return PlayerLevelDTO(
            player_id=entry.player_id,
            level=entry.level,
            wins=entry.wins,
            losses=entry.losses,
        )

