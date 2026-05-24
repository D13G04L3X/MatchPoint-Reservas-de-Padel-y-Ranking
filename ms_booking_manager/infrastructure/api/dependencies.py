from functools import lru_cache

from fastapi import Depends
from sqlalchemy.ext.asyncio import AsyncSession

from application.use_cases.cancel_booking import CancelBookingUseCase
from application.use_cases.create_booking import CreateBookingUseCase
from application.use_cases.get_availability import GetCourtAvailabilityUseCase
from domain.ports.booking_repository import BookingRepository
from infrastructure.clients.identity_http_client import IdentityHttpClient
from infrastructure.clients.ranking_http_client import RankingHttpClient
from infrastructure.messaging.rabbitmq_publisher import RabbitMQEventPublisher
from infrastructure.persistence.database import get_db
from infrastructure.persistence.postgres_booking_repository import PostgresBookingRepository


def get_booking_repository(
    session: AsyncSession = Depends(get_db),
) -> BookingRepository:
    """Provide a booking repository bound to the current session."""

    return PostgresBookingRepository(session)


@lru_cache
def get_identity_client() -> IdentityHttpClient:
    """Provide a shared Identity HTTP client."""

    return IdentityHttpClient()


@lru_cache
def get_ranking_client() -> RankingHttpClient:
    """Provide a shared Ranking HTTP client."""

    return RankingHttpClient()


@lru_cache
def get_event_publisher() -> RabbitMQEventPublisher:
    """Provide a shared RabbitMQ event publisher."""

    return RabbitMQEventPublisher()


def get_booking_use_case(
    booking_repository: BookingRepository = Depends(get_booking_repository),
    identity_client: IdentityHttpClient = Depends(get_identity_client),
    ranking_client: RankingHttpClient = Depends(get_ranking_client),
    event_publisher: RabbitMQEventPublisher = Depends(get_event_publisher),
) -> CreateBookingUseCase:
    """Provide the create booking use case."""

    return CreateBookingUseCase(
        booking_repository=booking_repository,
        identity_client=identity_client,
        ranking_client=ranking_client,
        event_publisher=event_publisher,
    )


def get_cancel_use_case(
    booking_repository: BookingRepository = Depends(get_booking_repository),
    event_publisher: RabbitMQEventPublisher = Depends(get_event_publisher),
) -> CancelBookingUseCase:
    """Provide the cancel booking use case."""

    return CancelBookingUseCase(
        booking_repository=booking_repository,
        event_publisher=event_publisher,
    )


def get_availability_use_case(
    booking_repository: BookingRepository = Depends(get_booking_repository),
) -> GetCourtAvailabilityUseCase:
    """Provide the availability use case."""

    return GetCourtAvailabilityUseCase(booking_repository=booking_repository)

