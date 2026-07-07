from __future__ import annotations

from opentelemetry import trace
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import ConsoleSpanExporter, SimpleSpanProcessor

from packages.telemetry.langfuse_exporter import init_langfuse_exporter

_tracer: trace.Tracer | None = None


def init_telemetry(service_name: str = "spark-v2") -> trace.Tracer:
    """Initialize OTel with console + optional Langfuse exporters."""
    global _tracer

    resource = Resource.create({"service.name": service_name})
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(SimpleSpanProcessor(ConsoleSpanExporter()))

    langfuse = init_langfuse_exporter()
    if langfuse:
        provider.add_span_processor(langfuse)

    trace.set_tracer_provider(provider)
    _tracer = trace.get_tracer(service_name)
    return _tracer


def get_tracer() -> trace.Tracer:
    """Get the global tracer, initializing if needed."""
    global _tracer
    if _tracer is None:
        _tracer = init_telemetry()
    return _tracer
