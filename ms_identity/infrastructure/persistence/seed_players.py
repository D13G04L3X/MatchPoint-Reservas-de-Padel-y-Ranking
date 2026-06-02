import logging
from datetime import datetime, timedelta, timezone

from sqlalchemy import select
from sqlalchemy.ext.asyncio import AsyncSession

from domain.models.enums import MembershipStatus, PlanType
from infrastructure.persistence.models import MembershipORM, PlayerORM

logger = logging.getLogger(__name__)

DEFAULT_PLAYERS: list[dict] = [
    {
        "id": "258eddc0-881a-4a95-a89d-fb369d526ff3",
        "username": "carlos_andrade",
        "email": "carlos@matchpoint.com",
        "level": 5.0,
        "membership_status": MembershipStatus.ACTIVE,
        "restriction_active": False,
        "restriction_until": None,
        "plan_type": PlanType.PREMIUM,
        "memb_active": True,
        "memb_id": "a0000001-0000-4000-8000-000000000001",
    },
    {
        "id": "365a0b54-0c23-4c4a-8c08-0bf13a23c202",
        "username": "ana_garcia",
        "email": "ana@matchpoint.com",
        "level": 4.5,
        "membership_status": MembershipStatus.ACTIVE,
        "restriction_active": False,
        "restriction_until": None,
        "plan_type": PlanType.PREMIUM,
        "memb_active": True,
        "memb_id": "a0000002-0000-4000-8000-000000000002",
    },
    {
        "id": "7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d",
        "username": "pedro_ruiz",
        "email": "pedro@matchpoint.com",
        "level": 4.8,
        "membership_status": MembershipStatus.ACTIVE,
        "restriction_active": False,
        "restriction_until": None,
        "plan_type": PlanType.PREMIUM,
        "memb_active": True,
        "memb_id": "a0000003-0000-4000-8000-000000000003",
    },
    {
        "id": "5caea60a-3582-40ae-a9e0-d83def672f4d",
        "username": "laura_mendez",
        "email": "laura@matchpoint.com",
        "level": 3.0,
        "membership_status": MembershipStatus.ACTIVE,
        "restriction_active": False,
        "restriction_until": None,
        "plan_type": PlanType.BASIC,
        "memb_active": True,
        "memb_id": "a0000004-0000-4000-8000-000000000004",
    },
    {
        "id": "82d54dde-e2ff-4732-9e20-9d724fe47005",
        "username": "mario_vega",
        "email": "mario@matchpoint.com",
        "level": 6.2,
        "membership_status": MembershipStatus.EXPIRED,
        "restriction_active": False,
        "restriction_until": None,
        "plan_type": PlanType.BASIC,
        "memb_active": False,
        "memb_id": "a0000005-0000-4000-8000-000000000005",
    },
    {
        "id": "4dd9cff3-bb91-4b43-93c8-1b221a7669ab",
        "username": "sofia_torres",
        "email": "sofia@matchpoint.com",
        "level": 4.0,
        "membership_status": MembershipStatus.ACTIVE,
        "restriction_active": True,
        "restriction_until": datetime.now(timezone.utc) + timedelta(days=7),
        "plan_type": PlanType.PREMIUM,
        "memb_active": True,
        "memb_id": "a0000006-0000-4000-8000-000000000006",
    },
]

async def seed_default_players(session: AsyncSession) -> None:
    for p in DEFAULT_PLAYERS:
        existing = await session.execute(
            select(PlayerORM).where(PlayerORM.email == p["email"])
        )
        row = existing.scalar_one_or_none()
        if row is not None:
            continue

        player = PlayerORM(
            id=p["id"],
            username=p["username"],
            email=p["email"],
            level=p["level"],
            membership_status=p["membership_status"],
            restriction_active=p["restriction_active"],
            restriction_until=p["restriction_until"],
        )
        session.add(player)

    await session.flush()

    for p in DEFAULT_PLAYERS:
        result = await session.execute(
            select(MembershipORM).where(MembershipORM.player_id == p["id"])
        )
        if result.scalar_one_or_none() is not None:
            continue

        membership = MembershipORM(
            id=p["memb_id"],
            player_id=p["id"],
            plan_type=p["plan_type"],
            valid_until=datetime.now(timezone.utc) + timedelta(days=365),
            is_active=p["memb_active"],
        )
        session.add(membership)

    await session.commit()

    count = len(DEFAULT_PLAYERS)
    logger.info("Seeded %d default players with memberships", count)
