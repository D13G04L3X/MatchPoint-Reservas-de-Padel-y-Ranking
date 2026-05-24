from __future__ import annotations

import json
from datetime import datetime
from typing import Protocol
from uuid import UUID

import aio_pika
from aio_pika import ExchangeType, IncomingMessage, RobustChannel, RobustConnection

from config import settings

import logging
logger = logging.getLogger(__name__)

class UpdatePlayerRestrictionUseCasePort(Protocol):
    """Protocol for updating player restrictions from events."""

    async def execute(self, player_id: UUID, restriction_until: datetime) -> None:
        """Update the player restriction state."""


class RabbitMQIdentityConsumer:
    """RabbitMQ consumer for restriction events."""

    def __init__(
        self, use_case: UpdatePlayerRestrictionUseCasePort, rabbitmq_url: str | None = None
    ) -> None:
        self._use_case = use_case
        self._rabbitmq_url = rabbitmq_url or settings.RABBITMQ_URL
        self._connection: RobustConnection | None = None
        self._channel: RobustChannel | None = None
        self._queue_name = "identity.queue"

    async def start(self) -> None:
        try:
            self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
            self._channel = await self._connection.channel()

            exchange = await self._channel.declare_exchange(
                "matchpoint.events", ExchangeType.TOPIC, durable=True
            )
            queue = await self._channel.declare_queue(self._queue_name, durable=True)
            await queue.bind(exchange, routing_key="user.restricted")
            await queue.consume(self._on_message)
            logger.info("RabbitMQ identity consumer started")
        except Exception as e:
            logger.warning("RabbitMQ unavailable, identity consumer not started: %s", e)

    async def stop(self) -> None:
        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()

    async def _on_message(self, message: IncomingMessage) -> None:
        try:
            payload = json.loads(message.body.decode("utf-8"))
            player_id = UUID(payload["player_id"])
            restriction_until = datetime.fromisoformat(payload["restriction_until"])

            await self._use_case.execute(
                player_id=player_id, restriction_until=restriction_until
            )
            await message.ack()
        except Exception:
            await message.nack(requeue=False)

