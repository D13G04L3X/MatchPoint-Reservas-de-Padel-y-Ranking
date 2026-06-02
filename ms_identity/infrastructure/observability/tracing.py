import logging
from fastapi import FastAPI

logger = logging.getLogger(__name__)


def configure_tracing(service_name: str, otlp_endpoint: str) -> None:
    """Configure OpenTelemetry provider and exporter."""
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.propagate import set_global_textmap
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)
        provider.add_span_processor(
            BatchSpanProcessor(OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True))
        )
        set_global_textmap(TraceContextTextMapPropagator())
        logger.info("Tracing configured: %s -> %s", service_name, otlp_endpoint)

    except Exception as e:
        logger.warning("Tracing provider unavailable, skipping: %s", e)


def instrument_app(app: FastAPI) -> None:
    """Instrument FastAPI app — must be called before app starts."""
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        FastAPIInstrumentor().instrument_app(app)
        HTTPXClientInstrumentor().instrument()
        logger.info("FastAPI instrumentation applied")
    except Exception as e:
        logger.warning("FastAPI instrumentation unavailable: %s", e)