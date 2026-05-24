from dataclasses import dataclass
from datetime import datetime
from uuid import UUID


@dataclass(frozen=True)
class AuditLog:
    """Audit log entry for processed events.

    Fields:
        event_id: Unique event identifier.
        event_type: Event type or routing key.
        payload: Raw event payload for traceability.
        processed_at: Timestamp when the event was processed.
    """

    event_id: UUID
    event_type: str
    payload: dict[str, object]
    processed_at: datetime

    def __post_init__(self) -> None:
        if not isinstance(self.event_id, UUID):
            raise TypeError("AuditLog event_id must be a UUID.")
        if not isinstance(self.event_type, str) or not self.event_type.strip():
            raise ValueError("AuditLog event_type must be a non-empty string.")
        if not isinstance(self.payload, dict):
            raise TypeError("AuditLog payload must be a dict.")
        if not isinstance(self.processed_at, datetime):
            raise TypeError("AuditLog processed_at must be a datetime.")

