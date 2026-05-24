from pydantic_settings import BaseSettings, SettingsConfigDict
from pydantic import Field


class Settings(BaseSettings):
    DATABASE_URL: str = "postgresql+asyncpg://matchpoint:matchpoint@postgres:5432/bookingdb"
    IDENTITY_SERVICE_URL: str = "http://ms-identity:8082"
    PENALTY_SERVICE_URL: str = "http://ms-penalty-rank:8083"
    RABBITMQ_URL: str = "amqp://matchpoint:matchpoint@rabbitmq:5672/"
    OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://jaeger:4317"
    SERVICE_NAME: str = "ms-booking-manager"

    # Load values from .env when running under docker-compose
    model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()
