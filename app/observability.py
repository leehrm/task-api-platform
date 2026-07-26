import logging
import os
from contextlib import contextmanager

from fastapi import FastAPI
from opentelemetry import trace
from opentelemetry.exporter.otlp.proto.grpc.trace_exporter import OTLPSpanExporter
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.instrumentation.psycopg2 import Psycopg2Instrumentor
from opentelemetry.instrumentation.redis import RedisInstrumentor
from opentelemetry.sdk.resources import Resource
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import BatchSpanProcessor

from app import __version__


logger = logging.getLogger(__name__)

EXCLUDED_URLS = ",".join(
    (
        r".*/metrics$",
        r".*/healthz$",
        r".*/readyz$",
        r".*/docs$",
        r".*/redoc$",
        r".*/openapi\.json$",
        r".*/static/.*",
        r".*/internal/drain$",
    )
)
EXCLUDED_FASTAPI_SPANS = ["receive", "send"]

_configured = False


def configure_observability(app: FastAPI) -> None:
    global _configured
    if _configured or os.getenv("OTEL_SDK_DISABLED", "false").lower() == "true":
        return

    resource = Resource.create(
        {
            "service.name": os.getenv("OTEL_SERVICE_NAME", "task-api"),
            "service.version": os.getenv("APP_VERSION", __version__),
            "deployment.environment.name": os.getenv("APP_ENV", "local"),
            "k8s.namespace.name": os.getenv("POD_NAMESPACE", "unknown"),
            "k8s.pod.name": os.getenv("POD_NAME", "unknown"),
            "k8s.node.name": os.getenv("NODE_NAME", "unknown"),
        }
    )
    provider = TracerProvider(resource=resource)
    provider.add_span_processor(BatchSpanProcessor(OTLPSpanExporter()))
    trace.set_tracer_provider(provider)

    Psycopg2Instrumentor().instrument()
    RedisInstrumentor().instrument()
    FastAPIInstrumentor.instrument_app(
        app,
        excluded_urls=EXCLUDED_URLS,
        exclude_spans=EXCLUDED_FASTAPI_SPANS,
    )
    _configured = True
    logger.info("event=otel_initialized service=%s", os.getenv("OTEL_SERVICE_NAME", "task-api"))


def get_tracer():
    return trace.get_tracer("task-api")


@contextmanager
def trace_db_operation(operation: str, role: str, target: str):
    with get_tracer().start_as_current_span(f"task.db.{operation}") as span:
        span.set_attribute("db.role", role)
        span.set_attribute("db.target", target)
        yield span
