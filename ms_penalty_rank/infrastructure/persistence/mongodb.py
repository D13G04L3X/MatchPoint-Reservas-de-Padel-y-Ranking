from motor.motor_asyncio import AsyncIOMotorClient, AsyncIOMotorDatabase

from config import settings


_client = AsyncIOMotorClient(settings.MONGODB_URL)


def get_database() -> AsyncIOMotorDatabase:
    """Return the configured MongoDB database."""

    return _client[settings.MONGODB_DB]


async def init_indexes(database: AsyncIOMotorDatabase) -> None:
    """Create MongoDB indexes for penalty, ranking, and audit collections."""

    await database.penalties.create_index(
        [("player_id", 1), ("is_active", 1), ("expires_at", 1)]
    )
    await database.rankings.create_index("player_id", unique=True)
    await database.audit_logs.create_index("event_id", unique=True)

