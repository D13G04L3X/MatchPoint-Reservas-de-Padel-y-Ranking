from contextlib import asynccontextmanager
from fastapi import FastAPI
from starlette.middleware.wsgi import WSGIMiddleware

from config import settings
from infrastructure.api.booking_router import (
    booking_router,
    courts_router,
    internal_router,
)
from infrastructure.api.health_router import router as health_router
from infrastructure.api.dependencies import (
    get_event_publisher,
    get_identity_client,
    get_ranking_client,
)
from infrastructure.observability.metrics import MetricsMiddleware, get_metrics_app
from infrastructure.observability.tracing import configure_tracing, instrument_app
from infrastructure.persistence.database import init_db


@asynccontextmanager
async def lifespan(app: FastAPI):
    configure_tracing(settings.SERVICE_NAME, settings.OTEL_EXPORTER_OTLP_ENDPOINT)
    await init_db()
    yield
    await get_identity_client().close()
    await get_ranking_client().close()
    await get_event_publisher().close()


app = FastAPI(
    title="MS-BookingManager",
    version="1.0.0",
    docs_url="/docs",
    redoc_url="/redoc",
    lifespan=lifespan,
)

instrument_app(app)             # ← antes del middleware

app.add_middleware(MetricsMiddleware)
app.mount("/metrics", WSGIMiddleware(get_metrics_app()))

app.include_router(booking_router, prefix="/bookings", tags=["Bookings"])
app.include_router(courts_router, tags=["Courts"])
app.include_router(internal_router)
app.include_router(health_router)