from datetime import datetime
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException
from pydantic import BaseModel, Field

from application.dtos.membership_validation_response_dto import (
    MembershipValidationResponseDTO,
)
from application.dtos.player_list_item_dto import PlayerListItemDTO
from application.dtos.player_restriction_dto import PlayerRestrictionDTO
from application.use_cases.update_player_restriction import UpdatePlayerRestrictionUseCase
from application.use_cases.validate_membership import ValidateMembershipUseCase
from domain.ports.player_repository import PlayerRepository
from infrastructure.api.dependencies import (
    get_player_repository,
    get_update_restriction_use_case,
    get_validate_membership_use_case,
)
from infrastructure.observability.metrics import membership_validations_total, restriction_checks_total


class RestrictionUpdateDTO(BaseModel):
    """Payload for updating restrictions."""

    restriction_until: datetime | None = Field(
        None, description="Timestamp when restriction ends."
    )
    restriction_active: bool = Field(
        True, description="True when restriction is active."
    )


router = APIRouter(prefix="/internal", tags=["Internal"])


@router.get("/players", response_model=list[PlayerListItemDTO])
async def list_players(
    player_repository: PlayerRepository = Depends(get_player_repository),
) -> list[PlayerListItemDTO]:
    """List all players stored in identity."""

    players = await player_repository.list_all()
    return [
        PlayerListItemDTO(
            id=player.id,
            username=player.username,
            email=player.email,
            membership_status=player.membership_status,
            restriction_active=player.restriction_active,
            restriction_until=player.restriction_until,
        )
        for player in players
    ]


@router.get(
    "/membership/{player_id}/validate",
    response_model=MembershipValidationResponseDTO,
)
async def validate_membership(
    player_id: UUID,
    use_case: ValidateMembershipUseCase = Depends(get_validate_membership_use_case),
) -> MembershipValidationResponseDTO:
    """Validate membership for a player."""

    result = await use_case.execute(player_id)
    membership_validations_total.inc()
    return result


@router.get("/restriction/{player_id}")
async def get_restriction(
    player_id: UUID,
    player_repository: PlayerRepository = Depends(get_player_repository),
) -> dict[str, object]:
    """Return restriction status for a player."""

    player = await player_repository.get_by_id(player_id)
    if player is None:
        raise HTTPException(status_code=404, detail="Player not found.")
    restriction_checks_total.inc()
    return {
        "has_restriction": player.restriction_active,
        "restriction_until": player.restriction_until,
    }


@router.put("/restriction/{player_id}", response_model=PlayerRestrictionDTO)
async def update_restriction(
    player_id: UUID,
    dto: RestrictionUpdateDTO,
    use_case: UpdatePlayerRestrictionUseCase = Depends(get_update_restriction_use_case),
    player_repository: PlayerRepository = Depends(get_player_repository),
) -> PlayerRestrictionDTO:
    """Update restriction status for a player."""

    if dto.restriction_active:
        await use_case.execute(player_id, dto.restriction_until or datetime.utcnow())
    else:
        updated = await player_repository.update_restriction(
            player_id=player_id,
            restriction_active=False,
            restriction_until=dto.restriction_until,
        )
        return PlayerRestrictionDTO(
            player_id=updated.id,
            restriction_active=updated.restriction_active,
            restriction_until=updated.restriction_until,
        )

    updated = await player_repository.get_by_id(player_id)
    if updated is None:
        raise HTTPException(status_code=404, detail="Player not found.")
    return PlayerRestrictionDTO(
        player_id=updated.id,
        restriction_active=updated.restriction_active,
        restriction_until=updated.restriction_until,
    )


# Public router (no /internal prefix) for lightweight admin/debug reads
public_router = APIRouter(tags=["Players"])


@public_router.get("/players", response_model=list[PlayerListItemDTO])
async def public_list_players(
    player_repository: PlayerRepository = Depends(get_player_repository),
) -> list[PlayerListItemDTO]:
    """Public endpoint to list players (intended for debugging/demo)."""

    players = await player_repository.list_all()
    return [
        PlayerListItemDTO(
            id=player.id,
            username=player.username,
            email=player.email,
            membership_status=player.membership_status,
            restriction_active=player.restriction_active,
            restriction_until=player.restriction_until,
        )
        for player in players
    ]

