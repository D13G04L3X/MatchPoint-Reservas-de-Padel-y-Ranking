from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware

from config import settings
from infrastructure.api.health_router import router as health_router
from infrastructure.api.dependencies import get_apply_penalty_use_case, get_event_publisher
from infrastructure.api.penalty_rank_router import internal_router, public_router
from infrastructure.messaging.rabbitmq_consumer import RabbitMQPenaltyConsumer
from infrastructure.observability.metrics import MetricsMiddleware, get_metrics_app
from infrastructure.observability.tracing import configure_tracing, instrument_app
from infrastructure.persistence.mongodb import get_database, init_indexes
from infrastructure.persistence.seed_ranks import seed_default_ranks


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_tracing(settings.SERVICE_NAME, settings.OTEL_EXPORTER_OTLP_ENDPOINT)
    database = get_database()
    await init_indexes(database)
    await seed_default_ranks(database)

    consumer = RabbitMQPenaltyConsumer(get_apply_penalty_use_case())
    await consumer.start()

    try:
        yield
    finally:
        await consumer.stop()
        await get_event_publisher().close()


app = FastAPI(
    title="MS-PenaltyRank",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    root_path=settings.ROOT_PATH,
    lifespan=lifespan,
)

instrument_app(app) # ← antes del middleware

app.add_middleware(MetricsMiddleware)
app.mount("/metrics", WSGIMiddleware(get_metrics_app()))
app.include_router(internal_router)
app.include_router(public_router)
app.include_router(health_router)