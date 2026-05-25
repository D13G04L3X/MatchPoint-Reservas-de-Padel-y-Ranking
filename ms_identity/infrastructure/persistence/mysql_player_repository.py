from datetime import datetime
from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.membership import Membership
from domain.models.player import Player
from domain.ports.player_repository import PlayerRepository
from infrastructure.persistence.models import MembershipORM, PlayerORM


class MySQLPlayerRepository(PlayerRepository):
    """MySQL implementation of the player repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, orm: PlayerORM) -> Player:
        return Player(
            id=UUID(orm.id),
            username=orm.username,
            email=orm.email,
            membership_status=orm.membership_status,
            restriction_active=orm.restriction_active,
            restriction_until=orm.restriction_until,
        )

    def _to_orm(self, player: Player) -> PlayerORM:
        return PlayerORM(
            id=str(player.id),
            username=player.username,
            email=player.email,
            membership_status=player.membership_status,
            restriction_active=player.restriction_active,
            restriction_until=player.restriction_until,
        )

    def _membership_to_domain(self, orm: MembershipORM) -> Membership:
        return Membership(
            id=UUID(orm.id),
            player_id=UUID(orm.player_id),
            plan_type=orm.plan_type,
            valid_until=orm.valid_until,
            is_active=orm.is_active,
        )

    async def get_by_id(self, player_id: UUID) -> Player | None:
        result = await self._session.execute(
            select(PlayerORM).where(PlayerORM.id == str(player_id))
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

    async def list_all(self) -> list[Player]:
        result = await self._session.execute(select(PlayerORM).order_by(PlayerORM.username))
        rows = result.scalars().all()
        return [self._to_domain(orm) for orm in rows]

    async def update_restriction(
        self, player_id: UUID, restriction_active: bool, restriction_until: datetime | None
    ) -> Player:
        result = await self._session.execute(
            select(PlayerORM).where(PlayerORM.id == str(player_id))
        )
        orm = result.scalar_one_or_none()
        if orm is None:
            raise ValueError("Player not found.")

        orm.restriction_active = restriction_active
        orm.restriction_until = restriction_until
        await self._session.commit()
        await self._session.refresh(orm)
        return self._to_domain(orm)

    async def get_membership(self, player_id: UUID) -> Membership | None:
        result = await self._session.execute(
            select(MembershipORM).where(MembershipORM.player_id == str(player_id))
        )
        orm = result.scalar_one_or_none()
        return self._membership_to_domain(orm) if orm else None

