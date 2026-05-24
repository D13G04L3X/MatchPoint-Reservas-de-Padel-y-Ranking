from uuid import UUID

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.membership import Membership
from domain.ports.membership_repository import MembershipRepository
from infrastructure.persistence.models import MembershipORM


class MySQLMembershipRepository(MembershipRepository):
    """MySQL implementation of the membership repository."""

    def __init__(self, session: AsyncSession) -> None:
        self._session = session

    def _to_domain(self, orm: MembershipORM) -> Membership:
        return Membership(
            id=UUID(orm.id),
            player_id=UUID(orm.player_id),
            plan_type=orm.plan_type,
            valid_until=orm.valid_until,
            is_active=orm.is_active,
        )

    async def get_active_by_player(self, player_id: UUID) -> Membership | None:
        result = await self._session.execute(
            select(MembershipORM).where(
                MembershipORM.player_id == str(player_id),
                MembershipORM.is_active.is_(True),
            )
        )
        orm = result.scalar_one_or_none()
        return self._to_domain(orm) if orm else None

