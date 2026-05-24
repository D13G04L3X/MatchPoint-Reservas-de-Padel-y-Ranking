from datetime import datetime, timezone
from uuid import UUID

from fastapi import APIRouter, Depends
from pydantic import BaseModel, Field

from application.dtos.penalty_response_dto import PenaltyResponseDTO
from application.dtos.player_level_dto import PlayerLevelDTO
from application.dtos.ranking_list_dto import PlayerLevelEntry, RankingListDTO
from application.use_cases.get_player_level import GetPlayerLevelUseCase
from application.use_cases.get_players_levels_batch import GetPlayersLevelsBatchUseCase
from domain.ports.penalty_repository import PenaltyRepository
from domain.ports.rank_repository import RankRepository
from infrastructure.api.dependencies import (
    get_penalty_repository,
    get_player_level_use_case,
    get_players_levels_batch_use_case,
    get_rank_repository,
)


class RankBatchRequestDTO(BaseModel):
    """Batch request for rank levels."""

    player_ids: list[UUID] = Field(..., description="Player ids to resolve.")


internal_router = APIRouter(prefix="/internal", include_in_schema=False)
public_router = APIRouter()


@internal_router.get("/rank/{player_id}", response_model=PlayerLevelDTO)
async def get_player_rank(
    player_id: UUID,
    use_case: GetPlayerLevelUseCase = Depends(get_player_level_use_case),
) -> PlayerLevelDTO:
    """Return rank for a single player."""

    return await use_case.execute(player_id)


@internal_router.post("/rank/batch")
async def get_players_rank_batch(
    dto: RankBatchRequestDTO,
    use_case: GetPlayersLevelsBatchUseCase = Depends(get_players_levels_batch_use_case),
) -> dict[str, float]:
    """Return rank levels for multiple players."""

    levels = await use_case.execute(dto.player_ids)
    return {str(player_id): level for player_id, level in levels.items()}


@public_router.get("/ranking", response_model=RankingListDTO)
async def get_ranking(
    rank_repository: RankRepository = Depends(get_rank_repository),
) -> RankingListDTO:
    """Return the public ranking list."""

    entries = await rank_repository.list_ranked()
    sorted_entries = sorted(entries, key=lambda entry: entry.level, reverse=True)[:20]

    return RankingListDTO(
        entries=[
            PlayerLevelEntry(
                player_id=entry.player_id,
                level=entry.level,
                wins=entry.wins,
                losses=entry.losses,
            )
            for entry in sorted_entries
        ],
        generated_at=datetime.now(timezone.utc),
    )


@public_router.get("/penalties/{player_id}", response_model=list[PenaltyResponseDTO])
async def get_penalties(
    player_id: UUID,
    penalty_repository: PenaltyRepository = Depends(get_penalty_repository),
) -> list[PenaltyResponseDTO]:
    """Return active penalties for a player."""

    penalties = await penalty_repository.get_active_by_player(player_id)
    return [
        PenaltyResponseDTO(
            player_id=penalty.player_id,
            reason=penalty.reason,
            applied_at=penalty.applied_at,
            expires_at=penalty.expires_at,
            is_active=penalty.is_active,
        )
        for penalty in penalties
    ]

