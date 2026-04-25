"""
app/core/logging.py

Structured logging configuration.
- JSON format in production  (LOG_FORMAT=json)
- Human-readable format in development (LOG_FORMAT=text)
- Log level driven by settings.log_level
- Request ID injected into every log record via a context var + Filter
"""

from __future__ import annotations

import json
import logging
import logging.config
import sys
from contextvars import ContextVar
from typing import Any, override

# ---------------------------------------------------------------------------
# Request-ID context variable
# ---------------------------------------------------------------------------
# Set this at the start of every request (e.g. in a FastAPI middleware) so
# every log record emitted during that request carries the same ID.
#
# Usage:
#   from app.core.logging import request_id_ctx_var
#   request_id_ctx_var.set("abc-123")
# ---------------------------------------------------------------------------
request_id_ctx_var: ContextVar[str] = ContextVar("request_id", default="-")


# ---------------------------------------------------------------------------
# LogRecord attributes to exclude from JSON payload
# ---------------------------------------------------------------------------
_LOG_RECORD_ATTRS: frozenset[str] = frozenset({
    "args",
    "asctime",
    "created",
    "exc_info",
    "exc_text",
    "filename",
    "funcName",
    "levelname",
    "levelno",
    "lineno",
    "message",
    "module",
    "msecs",
    "msg",
    "name",
    "pathname",
    "process",
    "processName",
    "relativeCreated",
    "request_id",
    "stack_info",
    "taskName",
    "thread",
    "threadName",
})


# ---------------------------------------------------------------------------
# Custom log filter — injects request_id into every LogRecord
# ---------------------------------------------------------------------------
class RequestIDFilter(logging.Filter):
    """Attach the current request ID to every log record."""

    @override
    def filter(self, record: logging.LogRecord) -> bool:
        record.request_id = request_id_ctx_var.get()
        return True


# ---------------------------------------------------------------------------
# JSON formatter
# ---------------------------------------------------------------------------
class JSONFormatter(logging.Formatter):
    """
    Emit each log record as a single-line JSON object.

    Avoids a heavy dependency (python-json-logger) while remaining
    compatible with log-aggregation pipelines (Datadog, Loki, CloudWatch).
    """

    # Fields always present in the output
    BASE_FIELDS: tuple[str, ...] = (
        "asctime",
        "levelname",
        "name",
        "message",
        "request_id",
    )

    def __init__(self) -> None:
        super().__init__(datefmt="%Y-%m-%dT%H:%M:%S")

    @override
    def format(self, record: logging.LogRecord) -> str:
        record.message = record.getMessage()

        # ISO-8601 timestamp
        record.asctime = self.formatTime(record, self.datefmt)

        payload: dict[str, Any] = {
            "timestamp": record.asctime,
            "level": record.levelname,
            "logger": record.name,
            "message": record.message,
            "request_id": getattr(record, "request_id", "-"),
        }

        # Attach exception info when present
        if record.exc_info:
            payload["exc_info"] = self.formatException(record.exc_info)

        # Attach any extra fields passed via logger.info("msg", extra={...})
        for key, value in record.__dict__.items():
            if key not in _LOG_RECORD_ATTRS and not key.startswith("_"):
                payload[key] = value

        return json.dumps(payload, default=str)


# ---------------------------------------------------------------------------
# Text formatter (development)
# ---------------------------------------------------------------------------
TEXT_FORMAT = (
    "%(asctime)s | %(levelname)-8s | %(name)s | [%(request_id)s] | %(message)s"
)
TEXT_DATEFMT = "%Y-%m-%d %H:%M:%S"


# ---------------------------------------------------------------------------
# Public setup function
# ---------------------------------------------------------------------------
def setup_logging(log_level: str = "INFO", log_format: str = "text") -> None:
    """
    Configure the root logger and the ``app`` logger.

    Call this once at application startup, before any other code logs.

    Args:
        log_level:  One of DEBUG / INFO / WARNING / ERROR / CRITICAL.
                    Driven by ``settings.log_level``.
        log_format: ``"json"`` for production, ``"text"`` for development.
                    Driven by ``settings.log_format``.
    """
    numeric_level = logging.getLevelName(log_level.upper())
    if not isinstance(numeric_level, int):
        numeric_level = logging.INFO

    # Choose formatter
    if log_format.lower() == "json":
        formatter: logging.Formatter = JSONFormatter()
    else:
        formatter = logging.Formatter(fmt=TEXT_FORMAT, datefmt=TEXT_DATEFMT)

    # Console handler
    handler = logging.StreamHandler(sys.stdout)
    handler.setFormatter(formatter)
    handler.addFilter(RequestIDFilter())

    # Root logger — catch everything (third-party libs too)
    root = logging.getLogger()
    root.setLevel(numeric_level)
    root.handlers.clear()
    root.addHandler(handler)

    # Silence noisy libraries to WARNING unless we're in DEBUG
    if numeric_level > logging.DEBUG:
        for noisy in ("uvicorn.access", "httpx", "httpcore"):
            logging.getLogger(noisy).setLevel(logging.WARNING)

    logging.getLogger("app").info(
        "Logging configured",
        extra={"log_level": log_level, "log_format": log_format},
    )


# ---------------------------------------------------------------------------
# Convenience getter (mirrors the pattern used by other modules)
# ---------------------------------------------------------------------------
def get_logger(name: str) -> logging.Logger:
    """
    Return a logger scoped under the ``app`` namespace.

    Usage::

        from app.core.logging import get_logger
        logger = get_logger(__name__)
        logger.info("Something happened", extra={"user_id": "u-123"})
    """
    return logging.getLogger(name)
