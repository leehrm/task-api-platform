import logging
import sys

from opentelemetry import trace


class TraceContextFilter(logging.Filter):
    def filter(self, record: logging.LogRecord) -> bool:
        context = trace.get_current_span().get_span_context()
        if context.is_valid:
            record.trace_id = format(context.trace_id, "032x")
            record.span_id = format(context.span_id, "016x")
        else:
            record.trace_id = "0" * 32
            record.span_id = "0" * 16
        return True


def configure_logging() -> None:
    app_logger = logging.getLogger("app")
    if app_logger.handlers:
        return

    handler = logging.StreamHandler(sys.stdout)
    handler.addFilter(TraceContextFilter())
    handler.setFormatter(
        logging.Formatter(
            "timestamp=%(asctime)s level=%(levelname)s logger=%(name)s "
            "trace_id=%(trace_id)s span_id=%(span_id)s %(message)s"
        )
    )

    app_logger.addHandler(handler)
    app_logger.setLevel(logging.INFO)
    app_logger.propagate = False
