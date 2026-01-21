"""
Structured Logging for AG-ACE-BRIDGE

Provides consistent, structured logging across all modules.
Uses structlog for JSON-formatted, context-rich logs.
"""

import sys
import logging
from typing import Any, Optional
from datetime import datetime

import structlog
from structlog.types import Processor


def _add_timestamp(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add ISO timestamp to log events"""
    event_dict["timestamp"] = datetime.now().isoformat()
    return event_dict


def _add_service_name(
    logger: logging.Logger, method_name: str, event_dict: dict[str, Any]
) -> dict[str, Any]:
    """Add service name to log events"""
    event_dict["service"] = "ag-ace-bridge"
    return event_dict


def configure_logging(
    level: str = "INFO",
    json_format: bool = False,
    log_file: Optional[str] = None
) -> None:
    """
    Configure structured logging for the application.

    Args:
        level: Log level (DEBUG, INFO, WARNING, ERROR, CRITICAL)
        json_format: If True, output JSON; otherwise, human-readable
        log_file: Optional file path for log output
    """
    # Set up standard library logging
    logging.basicConfig(
        format="%(message)s",
        stream=sys.stdout,
        level=getattr(logging, level.upper()),
    )

    # Configure processors
    shared_processors: list[Processor] = [
        structlog.contextvars.merge_contextvars,
        structlog.stdlib.add_log_level,
        structlog.stdlib.add_logger_name,
        _add_timestamp,
        _add_service_name,
        structlog.stdlib.PositionalArgumentsFormatter(),
        structlog.processors.StackInfoRenderer(),
        structlog.processors.UnicodeDecoder(),
    ]

    if json_format:
        # JSON output for production
        processors = shared_processors + [
            structlog.processors.format_exc_info,
            structlog.processors.JSONRenderer(),
        ]
    else:
        # Human-readable output for development
        processors = shared_processors + [
            structlog.dev.ConsoleRenderer(colors=True),
        ]

    structlog.configure(
        processors=processors,
        wrapper_class=structlog.stdlib.BoundLogger,
        context_class=dict,
        logger_factory=structlog.stdlib.LoggerFactory(),
        cache_logger_on_first_use=True,
    )


def get_logger(name: str) -> structlog.stdlib.BoundLogger:
    """
    Get a structured logger with the given name.

    Args:
        name: Logger name (typically module name)

    Returns:
        Configured structlog logger

    Example:
        logger = get_logger("orchestrator")
        logger.info("task_started", task_id="123", type="code")
        logger.error("task_failed", task_id="123", error="timeout")
    """
    return structlog.get_logger(name)


def bind_context(**kwargs: Any) -> None:
    """
    Bind context variables that will be included in all subsequent logs.

    Args:
        **kwargs: Key-value pairs to bind

    Example:
        bind_context(task_id="123", pipeline_id="456")
        logger.info("processing")  # Will include task_id and pipeline_id
    """
    structlog.contextvars.bind_contextvars(**kwargs)


def clear_context() -> None:
    """Clear all bound context variables."""
    structlog.contextvars.clear_contextvars()


def unbind_context(*keys: str) -> None:
    """
    Unbind specific context variables.

    Args:
        *keys: Keys to unbind
    """
    structlog.contextvars.unbind_contextvars(*keys)


# Initialize default logging configuration
configure_logging(level="INFO", json_format=False)


# Convenience loggers for common modules
class Loggers:
    """Pre-configured loggers for common modules"""

    @staticmethod
    def orchestrator() -> structlog.stdlib.BoundLogger:
        return get_logger("orchestrator")

    @staticmethod
    def pipeline() -> structlog.stdlib.BoundLogger:
        return get_logger("pipeline")

    @staticmethod
    def adapter() -> structlog.stdlib.BoundLogger:
        return get_logger("adapter")

    @staticmethod
    def memory() -> structlog.stdlib.BoundLogger:
        return get_logger("memory")

    @staticmethod
    def registry() -> structlog.stdlib.BoundLogger:
        return get_logger("registry")

    @staticmethod
    def queue() -> structlog.stdlib.BoundLogger:
        return get_logger("queue")
