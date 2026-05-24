from functools import lru_cache

from motor.motor_asyncio import AsyncIOMotorDatabase

from application.use_cases.apply_penalty import ApplyPenaltyUseCase
from application.use_cases.get_player_level import GetPlayerLevelUseCase
from application.use_cases.get_players_levels_batch import GetPlayersLevelsBatchUseCase
from domain.ports.audit_repository import AuditRepository
from domain.ports.penalty_repository import PenaltyRepository
from domain.ports.rank_repository import RankRepository
from infrastructure.messaging.rabbitmq_publisher import RabbitMQEventPublisher
from infrastructure.persistence.mongodb import get_database
from infrastructure.persistence.mongo_audit_repository import MongoAuditRepository
from infrastructure.persistence.mongo_penalty_repository import MongoPenaltyRepository
from infrastructure.persistence.mongo_rank_repository import MongoRankRepository


@lru_cache
def get_mongo_database() -> AsyncIOMotorDatabase:
    """Provide the shared MongoDB database."""

    return get_database()


def get_penalty_repository() -> PenaltyRepository:
    """Provide the penalty repository."""

    return MongoPenaltyRepository(get_mongo_database())


def get_rank_repository() -> RankRepository:
    """Provide the rank repository."""

    return MongoRankRepository(get_mongo_database())


def get_audit_repository() -> AuditRepository:
    """Provide the audit repository."""

    return MongoAuditRepository(get_mongo_database())


@lru_cache
def get_event_publisher() -> RabbitMQEventPublisher:
    """Provide the RabbitMQ event publisher."""

    return RabbitMQEventPublisher()


def get_apply_penalty_use_case() -> ApplyPenaltyUseCase:
    """Provide the apply penalty use case."""

    return ApplyPenaltyUseCase(
        penalty_repository=get_penalty_repository(),
        rank_repository=get_rank_repository(),
        audit_repository=get_audit_repository(),
        event_publisher=get_event_publisher(),
    )


def get_player_level_use_case() -> GetPlayerLevelUseCase:
    """Provide the get player level use case."""

    return GetPlayerLevelUseCase(rank_repository=get_rank_repository())


def get_players_levels_batch_use_case() -> GetPlayersLevelsBatchUseCase:
    """Provide the batch player levels use case."""

    return GetPlayersLevelsBatchUseCase(rank_repository=get_rank_repository())

