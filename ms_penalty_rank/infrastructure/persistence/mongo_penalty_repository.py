from datetime import datetime, timezone
from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.models.enums import PenaltyReason
from domain.models.penalty import Penalty
from domain.ports.penalty_repository import PenaltyRepository


class MongoPenaltyRepository(PenaltyRepository):
    """MongoDB implementation of the penalty repository."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._collection = database.get_collection("penalties")

    def _to_document(self, penalty: Penalty) -> dict[str, object]:
        return {
            "id": str(penalty.id),
            "player_id": str(penalty.player_id),
            "reason": penalty.reason.value,
            "applied_at": penalty.applied_at,
            "expires_at": penalty.expires_at,
            "is_active": penalty.is_active,
        }

    def _to_domain(self, document: dict[str, object]) -> Penalty:
        return Penalty(
            id=UUID(str(document["id"])),
            player_id=UUID(str(document["player_id"])),
            reason=PenaltyReason(str(document["reason"])),
            applied_at=document["applied_at"],
            expires_at=document["expires_at"],
            is_active=bool(document["is_active"]),
        )

    async def create(self, penalty: Penalty) -> Penalty:
        await self._collection.insert_one(self._to_document(penalty))
        return penalty

    async def get_active_by_player(self, player_id: UUID) -> list[Penalty]:
        now = datetime.now(timezone.utc)
        cursor = self._collection.find(
            {
                "player_id": str(player_id),
                "is_active": True,
                "expires_at": {"$gt": now},
            }
        )
        documents = await cursor.to_list(length=None)
        return [self._to_domain(document) for document in documents]

