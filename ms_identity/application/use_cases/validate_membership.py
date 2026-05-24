from datetime import datetime, timezone
from uuid import UUID

from application.dtos.membership_validation_response_dto import (
    MembershipValidationResponseDTO,
)
from domain.ports.membership_repository import MembershipRepository
from domain.ports.player_repository import PlayerRepository


class ValidateMembershipUseCase:
    """Use case for validating membership and restriction status."""

    def __init__(
        self,
        membership_repository: MembershipRepository,
        player_repository: PlayerRepository,
    ) -> None:
        self._membership_repository = membership_repository
        self._player_repository = player_repository

    async def execute(self, player_id: UUID) -> MembershipValidationResponseDTO:
        """Validate membership status for a player."""

        membership = await self._membership_repository.get_active_by_player(player_id)
        player = await self._player_repository.get_by_id(player_id)

        now = datetime.now(timezone.utc)
        valid_until = membership.valid_until if membership else None
        if valid_until is not None and valid_until.tzinfo is None:
            now_compare = now.replace(tzinfo=None)
        else:
            now_compare = now

        is_active = bool(
            membership and membership.is_active and valid_until and valid_until > now_compare
        )
        has_restriction = bool(player.restriction_active) if player else False

        return MembershipValidationResponseDTO(
            player_id=player_id,
            is_active=is_active,
            plan_type=membership.plan_type if membership else None,
            valid_until=valid_until,
            has_restriction=has_restriction,
        )

