from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application.use_cases.update_player_restriction import UpdatePlayerRestrictionUseCase
from application.use_cases.validate_membership import ValidateMembershipUseCase
from domain.ports.membership_repository import MembershipRepository
from domain.ports.player_repository import PlayerRepository
from infrastructure.persistence.database import get_db
from infrastructure.persistence.mysql_membership_repository import MySQLMembershipRepository
from infrastructure.persistence.mysql_player_repository import MySQLPlayerRepository


def get_player_repository(
    session: AsyncSession = Depends(get_db),
) -> PlayerRepository:
    """Provide a player repository bound to the current session."""

    return MySQLPlayerRepository(session)


def get_membership_repository(
    session: AsyncSession = Depends(get_db),
) -> MembershipRepository:
    """Provide a membership repository bound to the current session."""

    return MySQLMembershipRepository(session)


def get_validate_membership_use_case(
    membership_repository: MembershipRepository = Depends(get_membership_repository),
    player_repository: PlayerRepository = Depends(get_player_repository),
) -> ValidateMembershipUseCase:
    """Provide the validate membership use case."""

    return ValidateMembershipUseCase(
        membership_repository=membership_repository,
        player_repository=player_repository,
    )


def get_update_restriction_use_case(
    player_repository: PlayerRepository = Depends(get_player_repository),
) -> UpdatePlayerRestrictionUseCase:
    """Provide the update restriction use case."""

    return UpdatePlayerRestrictionUseCase(player_repository)

