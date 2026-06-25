# -*- coding: utf-8 -*-
"""Small HTTP-level utilities shared across the package.

The generated ``evergis_api._generated.client`` logs every non-2xx
response as ``logger.error("HTTP {code} ...\\nServer response: ...")``
before raising. For status codes used as existence probes (404 to
mean "not found", 409 to mean "already exists", ...) those lines are
noise: the caller catches the error and treats it as data, not a
failure.

:func:`silence_status_codes` is a context manager that hides those
lines for the duration of a probe call, while letting genuinely
unexpected errors (5xx, network, unexpected 4xx) keep their full log.
"""

from __future__ import annotations

import logging
from contextlib import contextmanager
from typing import Iterator


_GENERATED_LOGGER = "evergis_api._generated.client"


class _StatusCodeFilter(logging.Filter):
    """Drop log records whose message starts with ``HTTP <code>``."""

    def __init__(self, codes: tuple[int, ...]) -> None:
        super().__init__()
        self._prefixes = tuple(f"HTTP {code} " for code in codes)

    def filter(self, record: logging.LogRecord) -> bool:
        msg = record.getMessage()
        return not any(msg.startswith(p) for p in self._prefixes)


@contextmanager
def silence_status_codes(*codes: int) -> Iterator[None]:
    """Suppress generated-client error logs for the given status codes.

    Use this around a request that intentionally probes for one of
    these codes (e.g. ``404`` for "does this exist?"). Only the log
    line is silenced; the underlying ``ApiClientError`` is still
    raised and must be handled by the caller.

    Example:
        >>> from evergis_tools._http import silence_status_codes
        >>> with silence_status_codes(404):
        ...     try:
        ...         resource = client.catalog.get_resource(path)
        ...     except ApiClientError as e:
        ...         if e.status_code != 404:
        ...             raise
        ...         resource = None
    """
    log = logging.getLogger(_GENERATED_LOGGER)
    flt = _StatusCodeFilter(codes)
    log.addFilter(flt)
    try:
        yield
    finally:
        log.removeFilter(flt)


__all__ = ["silence_status_codes"]
