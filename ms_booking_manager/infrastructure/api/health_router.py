from __future__ import annotations

from fastapi import APIRouter, status
from fastapi.responses import JSONResponse
from sqlalchemy import text

import aio_pika

from config import settings
from infrastructure.persistence.database import AsyncSessionLocal

router = APIRouter()


async def _check_database() -> bool:
    try:
        async with AsyncSessionLocal() as session:
            await session.execute(text("SELECT 1"))
        return True
    except Exception:
        return False


async def _check_rabbitmq() -> bool:
    try:
        connection = await aio_pika.connect_robust(settings.RABBITMQ_URL, timeout=3)
        await connection.close()
        return True
    except Exception:
        return False


@router.get("/health")
async def health_check() -> JSONResponse:
    """Return service health based on database and broker connectivity."""

    db_ok = await _check_database()
    rabbit_ok = await _check_rabbitmq()

    status_text = "healthy" if db_ok and rabbit_ok else "degraded"
    status_code = (
        status.HTTP_200_OK
        if status_text == "healthy"
        else status.HTTP_503_SERVICE_UNAVAILABLE
    )

    return JSONResponse(
        status_code=status_code,
        content={
            "status": status_text,
            "service": settings.SERVICE_NAME,
            "version": "1.0.0",
            "checks": {
                "database": "ok" if db_ok else "error",
                "rabbitmq": "ok" if rabbit_ok else "error",
            },
        },
    )

