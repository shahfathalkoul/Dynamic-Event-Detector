"""Structured JSON logging with correlation IDs and per-module levels."""

from __future__ import annotations

import json
import logging
import os
import sys
import time
import uuid
from contextvars import ContextVar
from typing import Any

# Correlation ID for request tracing
correlation_id: ContextVar[str] = ContextVar("correlation_id", default="")


class JSONFormatter(logging.Formatter):
    """Emit structured JSON log lines for aggregation systems."""

    def format(self, record: logging.LogRecord) -> str:
        log_entry: dict[str, Any] = {
            "timestamp": self.formatTime(record, self.datefmt),
            "level": record.levelname,
            "logger": record.name,
            "message": record.getMessage(),
            "module": record.module,
            "function": record.funcName,
            "line": record.lineno,
        }

        cid = correlation_id.get("")
        if cid:
            log_entry["correlation_id"] = cid

        if record.exc_info and record.exc_info[1]:
            log_entry["exception"] = self.formatException(record.exc_info)

        # Include extra fields
        for key in ("event_id", "agent_name", "tool_name", "latency_ms", "cost_usd"):
            if hasattr(record, key):
                log_entry[key] = getattr(record, key)

        return json.dumps(log_entry, default=str)


def setup_logging(
    level: str = "INFO",
    json_output: bool | None = None,
) -> None:
    """Configure platform-wide logging.

    Parameters
    ----------
    level:
        Root log level (DEBUG, INFO, WARNING, ERROR).
    json_output:
        Force JSON output.  When ``None``, auto-detect: JSON in production,
        human-readable in development.
    """
    if json_output is None:
        json_output = os.environ.get("ENVIRONMENT", "development") != "development"

    root = logging.getLogger()
    root.setLevel(getattr(logging, level.upper(), logging.INFO))

    # Remove existing handlers
    for handler in root.handlers[:]:
        root.removeHandler(handler)

    handler = logging.StreamHandler(sys.stdout)
    if json_output:
        handler.setFormatter(JSONFormatter())
    else:
        handler.setFormatter(logging.Formatter(
            "%(asctime)s %(levelname)-8s [%(name)s] %(message)s",
            datefmt="%H:%M:%S",
        ))

    root.addHandler(handler)

    # Quiet noisy libraries
    for name in ("httpx", "httpcore", "urllib3", "uvicorn.access"):
        logging.getLogger(name).setLevel(logging.WARNING)
