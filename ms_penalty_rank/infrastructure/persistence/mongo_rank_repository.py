from datetime import datetime, timezone
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.models.rank_entry import RankEntry
from domain.ports.rank_repository import RankRepository


class MongoRankRepository(RankRepository):
    """MongoDB implementation of the rank repository."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._collection = database.get_collection("rankings")

    def _to_document(self, entry: RankEntry) -> dict[str, object]:
        return {
            "player_id": str(entry.player_id),
            "level": float(entry.level),
            "wins": entry.wins,
            "losses": entry.losses,
            "updated_at": entry.updated_at,
        }

    def _to_domain(self, document: dict[str, object]) -> RankEntry:
        return RankEntry(
            player_id=UUID(str(document["player_id"])),
            level=float(document["level"]),
            wins=int(document["wins"]),
            losses=int(document["losses"]),
            updated_at=document["updated_at"],
        )

    async def get_by_player(self, player_id: UUID) -> RankEntry | None:
        document = await self._collection.find_one({"player_id": str(player_id)})
        return self._to_domain(document) if document else None

    async def update_level(self, player_id: UUID, level: float) -> RankEntry:
        now = datetime.now(timezone.utc)
        await self._collection.update_one(
            {"player_id": str(player_id)},
            {
                "$set": {"level": float(level), "updated_at": now},
                "$setOnInsert": {
                    "player_id": str(player_id),
                    "wins": 0,
                    "losses": 0,
                },
            },
            upsert=True,
        )
        document = await self._collection.find_one({"player_id": str(player_id)})
        if document is None:
            raise ValueError("Rank entry not found.")
        return self._to_domain(document)

    async def list_ranked(self) -> list[RankEntry]:
        documents = await self._collection.find({}).to_list(length=None)
        return [self._to_domain(document) for document in documents]

