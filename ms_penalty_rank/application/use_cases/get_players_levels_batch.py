from uuid import UUID

from domain.ports.rank_repository import RankRepository


class GetPlayersLevelsBatchUseCase:
    """Use case for retrieving multiple player levels."""

    def __init__(self, rank_repository: RankRepository) -> None:
        self._rank_repository = rank_repository

    async def execute(self, player_ids: list[UUID]) -> dict[UUID, float]:
        """Return a mapping of player ids to their levels."""

        levels: dict[UUID, float] = {}
        for player_id in player_ids:
            entry = await self._rank_repository.get_by_player(player_id)
            if entry is None:
                entry = await self._rank_repository.update_level(player_id, 5.0)
            levels[player_id] = float(entry.level)
        return levels

