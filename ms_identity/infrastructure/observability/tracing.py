import logging

logger = logging.getLogger(__name__)


def configure_tracing(service_name: str, otlp_endpoint: str) -> None:
    """Configure OpenTelemetry tracing with OTLP gRPC exporter."""
    try:
        from opentelemetry import trace
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        from opentelemetry.propagate import set_global_textmap
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.trace.propagation.tracecontext import TraceContextTextMapPropagator

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        trace.set_tracer_provider(provider)

        exporter = OTLPSpanExporter(endpoint=otlp_endpoint)
        processor = BatchSpanProcessor(exporter)
        provider.add_span_processor(processor)

        set_global_textmap(TraceContextTextMapPropagator())

        FastAPIInstrumentor().instrument()
        HTTPXClientInstrumentor().instrument()

        logger.info("Tracing configured: %s -> %s", service_name, otlp_endpoint)

    except Exception as e:
        logger.warning("Tracing unavailable, skipping: %s", e)