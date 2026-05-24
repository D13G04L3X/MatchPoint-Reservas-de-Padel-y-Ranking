from uuid import UUID

from motor.motor_asyncio import AsyncIOMotorDatabase

from domain.models.audit_log import AuditLog
from domain.ports.audit_repository import AuditRepository


class MongoAuditRepository(AuditRepository):
    """MongoDB implementation of the audit repository."""

    def __init__(self, database: AsyncIOMotorDatabase) -> None:
        self._collection = database.get_collection("audit_logs")

    def _to_document(self, entry: AuditLog) -> dict[str, object]:
        return {
            "event_id": str(entry.event_id),
            "event_type": entry.event_type,
            "payload": entry.payload,
            "processed_at": entry.processed_at,
        }

    def _to_domain(self, document: dict[str, object]) -> AuditLog:
        return AuditLog(
            event_id=UUID(str(document["event_id"])),
            event_type=str(document["event_type"]),
            payload=document["payload"],
            processed_at=document["processed_at"],
        )

    async def log_event(self, entry: AuditLog) -> None:
        await self._collection.insert_one(self._to_document(entry))

    async def get_by_event_id(self, event_id: UUID) -> AuditLog | None:
        document = await self._collection.find_one({"event_id": str(event_id)})
        return self._to_domain(document) if document else None

