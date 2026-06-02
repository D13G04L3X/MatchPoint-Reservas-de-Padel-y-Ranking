from contextlib import asynccontextmanager

from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware

from application.use_cases.update_player_restriction import UpdatePlayerRestrictionUseCase
from config import settings
from infrastructure.api.health_router import router as health_router
from infrastructure.api.identity_router import router as identity_router, public_router as identity_public_router
from infrastructure.messaging.rabbitmq_consumer import RabbitMQIdentityConsumer
from infrastructure.observability.metrics import MetricsMiddleware, get_metrics_app
from infrastructure.observability.tracing import configure_tracing, instrument_app
from infrastructure.persistence.database import AsyncSessionLocal, init_db
from infrastructure.persistence.seed_players import seed_default_players
from infrastructure.persistence.mysql_player_repository import MySQLPlayerRepository


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_tracing(settings.SERVICE_NAME, settings.OTEL_EXPORTER_OTLP_ENDPOINT)
    await init_db()

    session = AsyncSessionLocal()
    await seed_default_players(session)
    restriction_use_case = UpdatePlayerRestrictionUseCase(MySQLPlayerRepository(session))
    consumer = RabbitMQIdentityConsumer(restriction_use_case)
    await consumer.start()

    try:
        yield
    finally:
        await consumer.stop()
        await session.close()


app = FastAPI(
    title="MS-Identity",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    root_path=settings.ROOT_PATH,
    lifespan=lifespan,
)

instrument_app(app)             # ← antes del middleware

app.add_middleware(MetricsMiddleware)
app.mount("/metrics", WSGIMiddleware(get_metrics_app()))
app.include_router(identity_router)
app.include_router(identity_public_router)
app.include_router(health_router)