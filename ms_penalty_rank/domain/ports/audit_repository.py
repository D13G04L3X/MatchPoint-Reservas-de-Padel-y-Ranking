from abc import ABC, abstractmethod
from uuid import UUID

from domain.models.audit_log import AuditLog


class AuditRepository(ABC):
    """Port for audit log persistence operations."""

    @abstractmethod
    async def log_event(self, entry: AuditLog) -> None:
        """Persist an audit log entry for an incoming event."""

    @abstractmethod
    async def get_by_event_id(self, event_id: UUID) -> AuditLog | None:
        """Return an audit log entry by event id, or None if missing."""

