import logging
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase

logger = logging.getLogger(__name__)

DEFAULT_RANKS: list[tuple[str, float, str]] = [
    ("258eddc0-881a-4a95-a89d-fb369d526ff3", 5.0, "carlos_andrade"),
    ("365a0b54-0c23-4c4a-8c08-0bf13a23c202", 4.5, "ana_garcia"),
    ("7a8b9c0d-1e2f-3a4b-5c6d-7e8f9a0b1c2d", 4.8, "pedro_ruiz"),
    ("5caea60a-3582-40ae-a9e0-d83def672f4d", 3.0, "laura_mendez"),
    ("82d54dde-e2ff-4732-9e20-9d724fe47005", 6.2, "mario_vega"),
    ("4dd9cff3-bb91-4b43-93c8-1b221a7669ab", 4.0, "sofia_torres"),
]

async def seed_default_ranks(database: AsyncIOMotorDatabase) -> None:
    from infrastructure.persistence.mongo_rank_repository import MongoRankRepository

    repo = MongoRankRepository(database)
    for player_id, level, username in DEFAULT_RANKS:
        existing = await database.rankings.find_one({"player_id": player_id})
        if existing is not None:
            continue
        await repo.update_level(UUID(player_id), level)

    count = len(DEFAULT_RANKS)
    logger.info("Seeded %d default ranks", count)
