"""OpenTelemetry tracing setup for the News Intelligence Platform.

Provides auto-instrumentation for FastAPI, SQLAlchemy, and HTTP clients,
plus custom span helpers for agent nodes and tool calls.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Generator

logger = logging.getLogger(__name__)


def setup_tracing(
    service_name: str | None = None,
    otlp_endpoint: str | None = None,
) -> None:
    """Initialize OpenTelemetry tracing with OTLP exporter.

    Call once at application startup.
    """
    service_name = service_name or os.environ.get("OTEL_SERVICE_NAME", "news-intelligence-api")
    otlp_endpoint = otlp_endpoint or os.environ.get("OTEL_EXPORTER_OTLP_ENDPOINT", "http://localhost:4317")

    try:
        from opentelemetry import trace
        from opentelemetry.sdk.trace import TracerProvider
        from opentelemetry.sdk.trace.export import BatchSpanProcessor
        from opentelemetry.sdk.resources import Resource
        from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter

        resource = Resource.create({"service.name": service_name})
        provider = TracerProvider(resource=resource)
        exporter = OTLPSpanExporter(endpoint=otlp_endpoint, insecure=True)
        provider.add_span_processor(BatchSpanProcessor(exporter))
        trace.set_tracer_provider(provider)

        # Auto-instrument libraries
        _instrument_fastapi()
        _instrument_sqlalchemy()
        _instrument_httpx()

        logger.info("OpenTelemetry tracing initialized (endpoint=%s)", otlp_endpoint)
    except ImportError:
        logger.info("OpenTelemetry not installed — tracing disabled.")
    except Exception as exc:
        logger.warning("Tracing setup failed: %s", exc)


def _instrument_fastapi() -> None:
    try:
        from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
        FastAPIInstrumentor().instrument()
    except ImportError:
        pass


def _instrument_sqlalchemy() -> None:
    try:
        from opentelemetry.instrumentation.sqlalchemy import SQLAlchemyInstrumentor
        SQLAlchemyInstrumentor().instrument()
    except ImportError:
        pass


def _instrument_httpx() -> None:
    try:
        from opentelemetry.instrumentation.httpx import HTTPXClientInstrumentor
        HTTPXClientInstrumentor().instrument()
    except ImportError:
        pass


def get_tracer(name: str = __name__):
    """Get a tracer instance for manual span creation."""
    try:
        from opentelemetry import trace
        return trace.get_tracer(name)
    except ImportError:
        return None


@contextmanager
def trace_span(
    name: str,
    attributes: dict | None = None,
) -> Generator:
    """Context manager for creating a custom span."""
    tracer = get_tracer()
    if tracer is None:
        yield None
        return

    with tracer.start_as_current_span(name) as span:
        if attributes:
            for key, value in attributes.items():
                span.set_attribute(key, str(value))
        yield span
