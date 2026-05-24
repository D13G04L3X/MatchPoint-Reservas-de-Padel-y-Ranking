from datetime import datetime, timedelta, timezone
from uuid import UUID, uuid4

from application.dtos.penalty_response_dto import PenaltyResponseDTO
from domain.models.audit_log import AuditLog
from domain.models.enums import PenaltyReason
from domain.models.penalty import Penalty
from domain.ports.audit_repository import AuditRepository
from domain.ports.event_publisher import EventPublisher
from domain.ports.penalty_repository import PenaltyRepository
from domain.ports.rank_repository import RankRepository


class ApplyPenaltyUseCase:
    """Use case for applying penalties with idempotent event processing."""

    def __init__(
        self,
        penalty_repository: PenaltyRepository,
        rank_repository: RankRepository,
        audit_repository: AuditRepository,
        event_publisher: EventPublisher,
    ) -> None:
        self._penalty_repository = penalty_repository
        self._rank_repository = rank_repository
        self._audit_repository = audit_repository
        self._event_publisher = event_publisher

    async def execute(
        self, player_id: UUID, reason: PenaltyReason, event_id: str
    ) -> PenaltyResponseDTO:
        """Apply a penalty if the event has not been processed."""

        event_uuid = UUID(event_id)
        existing = await self._audit_repository.get_by_event_id(event_uuid)
        if existing is not None:
            payload = existing.payload
            return PenaltyResponseDTO(
                player_id=UUID(str(payload.get("player_id"))),
                reason=PenaltyReason(str(payload.get("reason"))),
                applied_at=datetime.fromisoformat(str(payload.get("applied_at"))),
                expires_at=datetime.fromisoformat(str(payload.get("expires_at"))),
                is_active=bool(payload.get("is_active", True)),
            )

        now = datetime.now(timezone.utc)
        if reason == PenaltyReason.LATE_CANCELLATION:
            expires_at = now + timedelta(days=7)
        else:
            expires_at = now

        penalty = Penalty(
            id=uuid4(),
            player_id=player_id,
            reason=reason,
            applied_at=now,
            expires_at=expires_at,
            is_active=True,
        )
        await self._penalty_repository.create(penalty)

        payload = {
            "penalty_id": str(penalty.id),
            "player_id": str(player_id),
            "reason": penalty.reason.value,
            "applied_at": penalty.applied_at.isoformat(),
            "expires_at": penalty.expires_at.isoformat(),
            "is_active": penalty.is_active,
        }
        audit_entry = AuditLog(
            event_id=event_uuid,
            event_type="PENALTY_APPLIED",
            payload=payload,
            processed_at=now,
        )
        await self._audit_repository.log_event(audit_entry)
        await self._event_publisher.publish_user_restricted(player_id, expires_at)

        return PenaltyResponseDTO(
            player_id=player_id,
            reason=reason,
            applied_at=penalty.applied_at,
            expires_at=penalty.expires_at,
            is_active=penalty.is_active,
        )

