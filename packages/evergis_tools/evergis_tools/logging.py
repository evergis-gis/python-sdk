"""Centralized logging helpers for evergis_tools.

The helpers here avoid configuring global logging automatically. Call
``configure_logging`` from application code to attach handlers or use
``get_logger`` to obtain a namespaced logger that is safe to import even
when the host application manages logging itself.
"""

from __future__ import annotations

import logging
import os
from contextlib import contextmanager
from typing import Any, Dict, Optional

_DEFAULT_LEVEL_ENV = "EVERGIS_TOOLS_LOG_LEVEL"


def _resolve_level(level: Optional[str | int]) -> int:
    """Convert string/int levels to logging constants."""
    if level is None:
        env_level = os.getenv(_DEFAULT_LEVEL_ENV)
        if env_level:
            level = env_level
    if isinstance(level, str):
        level = level.upper()
        if level.isdigit():
            return int(level)
        return logging.getLevelName(level) if isinstance(logging.getLevelName(level), int) else logging.INFO
    if isinstance(level, int):
        return level
    return logging.INFO


def get_logger(name: Optional[str] = None) -> logging.Logger:
    """Return a configured logger with a NullHandler attached by default."""
    logger = logging.getLogger(name if name else "evergis_tools")
    if not logger.handlers:
        logger.addHandler(logging.NullHandler())
    return logger


def configure_logging(
    *,
    level: Optional[str | int] = None,
    formatter: Optional[logging.Formatter] = None,
    handler: Optional[logging.Handler] = None,
    extra_handlers: Optional[list[logging.Handler]] = None,
    propagate: Optional[bool] = None,
) -> logging.Logger:
    """Configure the root evergis_tools logger.

    Users can call this once in their applications to attach handlers and levels.
    """
    logger = logging.getLogger("evergis_tools")
    resolved_level = _resolve_level(level)
    logger.setLevel(resolved_level)

    for existing in list(logger.handlers):
        logger.removeHandler(existing)

    primary_handler = handler or logging.StreamHandler()
    if formatter:
        primary_handler.setFormatter(formatter)
    logger.addHandler(primary_handler)

    if extra_handlers:
        for extra in extra_handlers:
            logger.addHandler(extra)

    if propagate is not None:
        logger.propagate = propagate

    return logger


@contextmanager
def temporary_level(logger: logging.Logger, level: Optional[str | int]) -> Any:
    """Temporarily set the level for a logger within a context."""
    if level is None:
        yield
        return
    original = logger.level
    logger.setLevel(_resolve_level(level))
    try:
        yield
    finally:
        logger.setLevel(original)


def as_adapter(logger: logging.Logger, extra: Optional[Dict[str, Any]] = None) -> logging.LoggerAdapter:
    """Wrap the logger with contextual metadata."""
    return logging.LoggerAdapter(logger, extra or {})
