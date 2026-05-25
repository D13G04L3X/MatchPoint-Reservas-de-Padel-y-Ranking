from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
	"""Configuration for ms-penalty-rank."""

	MONGODB_URL: str = "mongodb://mongodb:27017"
	MONGODB_DB: str = "penaltyrank"
	RABBITMQ_URL: str = "amqp://matchpoint:matchpoint@rabbitmq:5672/"
	OTEL_EXPORTER_OTLP_ENDPOINT: str = "http://otel-collector:4317"
	SERVICE_NAME: str = "ms-penalty-rank"
	ROOT_PATH: str = "/penalty"

	# Load values from .env when running under docker-compose
	model_config = SettingsConfigDict(env_file=".env", env_file_encoding="utf-8", extra="ignore")


settings = Settings()

