import json
from datetime import datetime
from uuid import UUID

import aio_pika
from aio_pika import DeliveryMode, ExchangeType, Message, RobustChannel, RobustConnection

from config import settings
from domain.ports.event_publisher import EventPublisher


class RabbitMQEventPublisher(EventPublisher):
    """RabbitMQ publisher for penalty rank events."""

    def __init__(self, rabbitmq_url: str | None = None) -> None:
        self._rabbitmq_url = rabbitmq_url or settings.RABBITMQ_URL
        self._connection: RobustConnection | None = None
        self._channel: RobustChannel | None = None
        self._exchange: aio_pika.Exchange | None = None

    async def _get_exchange(self) -> aio_pika.Exchange:
        if self._connection is None or self._connection.is_closed:
            self._connection = await aio_pika.connect_robust(self._rabbitmq_url)
        if self._channel is None or self._channel.is_closed:
            self._channel = await self._connection.channel()
        if self._exchange is None:
            self._exchange = await self._channel.declare_exchange(
                "matchpoint.events", ExchangeType.TOPIC, durable=True
            )
        return self._exchange

    async def close(self) -> None:
        """Close the RabbitMQ channel and connection."""

        if self._channel and not self._channel.is_closed:
            await self._channel.close()
        if self._connection and not self._connection.is_closed:
            await self._connection.close()

    async def publish_user_restricted(self, player_id: UUID, restriction_until: datetime) -> None:
        exchange = await self._get_exchange()
        payload = {
            "player_id": str(player_id),
            "restriction_until": restriction_until.isoformat(),
        }
        body = json.dumps(payload).encode("utf-8")
        message = Message(
            body=body,
            content_type="application/json",
            delivery_mode=DeliveryMode.PERSISTENT,
        )
        await exchange.publish(message, routing_key="user.restricted")

