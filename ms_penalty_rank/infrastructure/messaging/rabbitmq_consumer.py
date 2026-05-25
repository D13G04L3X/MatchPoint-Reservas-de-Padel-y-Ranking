from __future__ import annotations

import json
from typing import Protocol
from uuid import UUID

import aio_pika
from aio_pika import ExchangeType, IncomingMessage, RobustChannel, RobustConnection

from config import settings
from domain.models.enums import PenaltyReason
from infrastructure.observability.metrics import penalties_applied_total

import logging
logger = logging.getLogger(__name__)

class ApplyPenaltyUseCasePort(Protocol):
    """Protocol for applying a penalty based on a cancellation event."""

    async def execute(
        self, player_id: UUID, reason: PenaltyReason, event_id: str
    ) -> object:
        """Apply penalty for a late cancellation event."""


class RabbitMQPenaltyConsumer:
    """RabbitMQ consumer for late cancellation events."""

    def __init__(self, use_case: ApplyPenaltyUseCasePort, rabbitmq_url: str | None = None) -> None:
        self._use_case = use_case
        self._rabbitmq_url = rabbitmq_url or settings.RABBITMQ_URL
        self._connection: RobustConnection | None = None
        self._channel: RobustChannel | None = None
        self._queue_name = "penalty.queue"

    async def start(self) -> None:
        try:
            self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
            self._channel = await self._connection.channel()

            exchange = await self._channel.declare_exchange(
                "matchpoint.events", ExchangeType.TOPIC, durable=True
            )
            queue = await self._channel.declare_queue(self._queue_name, durable=True)
            await queue.bind(exchange, routing_key="reservation.cancelled.late")
            await queue.consume(self._on_message)
            logger.info("RabbitMQ penalty consumer started")
        except Exception as e:
            logger.warning("RabbitMQ unavailable, penalty consumer not started: %s", e)

    async def stop(self) -> None:
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()

    async def _on_message(self, message: IncomingMessage) -> None:
        try:
            payload = json.loads(message.body.decode("utf-8"))
            event_id = str(payload["event_id"])
            player_id = UUID(payload["player_id"])

            await self._use_case.execute(
                player_id=player_id,
                reason=PenaltyReason.LATE_CANCELLATION,
                event_id=event_id,
            )
            penalties_applied_total.inc()
            await message.ack()
        except Exception:
            await message.nack(requeue=False)

