from fastapi import FastAPI, HTTPException
from fastapi.testclient import TestClient
from opentelemetry.instrumentation.fastapi import FastAPIInstrumentor
from opentelemetry.sdk.trace import TracerProvider
from opentelemetry.sdk.trace.export import SimpleSpanProcessor
from opentelemetry.sdk.trace.export.in_memory_span_exporter import InMemorySpanExporter
from opentelemetry.trace import SpanKind, StatusCode

from app.observability import EXCLUDED_FASTAPI_SPANS, EXCLUDED_URLS, trace_db_operation


def test_required_paths_are_excluded():
    for path in (
        "metrics",
        "healthz",
        "readyz",
        "docs",
        "redoc",
        r"openapi\.json",
        "static",
        "internal/drain",
    ):
        assert path in EXCLUDED_URLS


def test_version_is_traced():
    assert "version" not in EXCLUDED_URLS


def _instrumented_client():
    exporter = InMemorySpanExporter()
    provider = TracerProvider()
    provider.add_span_processor(SimpleSpanProcessor(exporter))
    application = FastAPI()

    @application.get("/ok")
    def ok():
        return {"status": "ok"}

    @application.get("/missing")
    def missing():
        raise HTTPException(status_code=404, detail="missing")

    @application.get("/error")
    def error():
        raise HTTPException(status_code=500, detail="error")

    @application.get("/healthz")
    def healthz():
        return {"status": "ok"}

    FastAPIInstrumentor.instrument_app(
        application,
        tracer_provider=provider,
        excluded_urls=EXCLUDED_URLS,
        exclude_spans=EXCLUDED_FASTAPI_SPANS,
    )
    return TestClient(application, raise_server_exceptions=False), exporter


def _server_span(exporter, path: str):
    return next(
        span
        for span in exporter.get_finished_spans()
        if span.kind is SpanKind.SERVER
        and (span.attributes.get("url.path") or span.attributes.get("http.target")) == path
    )


def test_fastapi_status_policy():
    client, exporter = _instrumented_client()

    assert client.get("/ok").status_code == 200
    assert client.get("/missing").status_code == 404
    assert client.get("/error").status_code == 500

    assert _server_span(exporter, "/ok").status.status_code is StatusCode.UNSET
    assert _server_span(exporter, "/missing").status.status_code is StatusCode.UNSET
    assert _server_span(exporter, "/error").status.status_code is StatusCode.ERROR


def test_fastapi_internal_send_receive_spans_are_excluded():
    client, exporter = _instrumented_client()

    assert client.get("/ok").status_code == 200
    assert all(
        not span.name.endswith(("http send", "http receive"))
        for span in exporter.get_finished_spans()
    )


def test_health_path_does_not_create_server_span():
    client, exporter = _instrumented_client()

    assert client.get("/healthz").status_code == 200
    assert not any(span.kind is SpanKind.SERVER for span in exporter.get_finished_spans())


def test_db_operation_attributes_are_added():
    span = Mock()
    span_context = Mock()
    span_context.__enter__ = Mock(return_value=span)
    span_context.__exit__ = Mock(return_value=False)
    tracer = Mock()
    tracer.start_as_current_span.return_value = span_context

    with patch("app.observability.get_tracer", return_value=tracer):
        with trace_db_operation("list_tasks", "read", "replica"):
            pass

    span.set_attribute.assert_any_call("db.role", "read")
    span.set_attribute.assert_any_call("db.target", "replica")
from unittest.mock import Mock, patch
