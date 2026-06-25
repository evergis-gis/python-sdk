# -*- coding: utf-8 -*-
"""Typed exception classes and predicates for ``ApiClientError`` status codes.

The autogen ``ApiClientError`` carries ``status_code`` already, so any
caller can write ``exc.status_code == 404``. Two reasons this module
exists anyway:

* Substring-match anti-pattern. Before this module several places
  matched on the rendered message text (``"409" in str(exc)``,
  ``"already exist" in str(exc)``). That breaks the moment the server
  changes its error wording. The predicates here use the structured
  HTTP status code instead.

* ``isinstance`` boundaries. ``ResourceNotFound``/``ResourceExists``/
  ``ApiTransientError`` are subclasses of ``ApiClientError`` so that
  wrappers which DO know the contextual meaning of a 404/409 (e.g.
  ``resolve_resource`` could raise ``ResourceNotFound`` instead of a
  generic 404) can opt into that. Existing ``except ApiClientError``
  blocks keep working because of subclassing.

Pair with :func:`evergis_tools._http.silence_status_codes` for probes
that intentionally trigger one of these codes.
"""

from __future__ import annotations

from typing import Optional

from evergis_api._generated.exceptions import ApiClientError


class ResourceNotFound(ApiClientError):
    """Resource not found - an HTTP 404, or a logical miss (e.g. an empty
    result set) that did not come from a 404 response.

    Constructible either from a real 404 (pass ``request``/``response``) or
    with just a message. ``status_code`` is always 404 and ``is_not_found``
    recognises it. ``__str__`` leads with the message, appending the raw HTTP
    line in brackets when there was an underlying response.
    """

    def __init__(self, message: str, *, request=None, response=None):
        if request is not None and response is not None:
            super().__init__(message, request=request, response=response)
        else:
            # Logical not-found without an HTTP 404 behind it.
            Exception.__init__(self, message)
            self.request = request
            self.response = response
            self.status_code = 404
            self.url = None
            self.method = None
            self.response_text = None
            self.response_headers = {}
            self.response_json = None

    def __str__(self) -> str:
        message = self.args[0] if self.args else ""
        if self.response is None:
            return message
        http_detail = super().__str__()
        if message and message not in http_detail:
            return f"{message} [{http_detail}]"
        return http_detail


class ResourceExists(ApiClientError):
    """Target system name or alias already taken - an HTTP 409, or a logical
    conflict caught by a pre-check before the request is even sent.

    Constructible from a real 409 (pass ``request``/``response``) or with just
    a message. ``status_code`` is always 409 and ``is_conflict`` recognises it.
    Unlike the base ``ApiClientError`` (whose ``__str__`` shows only the raw
    ``HTTP 409 ...`` line), this surfaces the actionable message the wrapper
    built - which alias/folder collided - appending the raw HTTP line in
    brackets when there was an underlying response.
    """

    def __init__(self, message: str, *, request=None, response=None):
        if request is not None and response is not None:
            super().__init__(message, request=request, response=response)
        else:
            # Logical conflict without an HTTP 409 behind it (pre-check).
            Exception.__init__(self, message)
            self.request = request
            self.response = response
            self.status_code = 409
            self.url = None
            self.method = None
            self.response_text = None
            self.response_headers = {}
            self.response_json = None

    def __str__(self) -> str:
        message = self.args[0] if self.args else ""
        if self.response is None:
            return message
        http_detail = super().__str__()
        if message and message not in http_detail:
            return f"{message} [{http_detail}]"
        return http_detail


class ApiTransientError(ApiClientError):
    """5xx from EverGIS - server-side, usually safe to retry."""


def _status_code(exc: BaseException) -> Optional[int]:
    return getattr(exc, "status_code", None)


def is_not_found(exc: BaseException) -> bool:
    """True if ``exc`` is an HTTP 404 from the EverGIS API client."""
    return isinstance(exc, ResourceNotFound) or _status_code(exc) == 404


def is_conflict(exc: BaseException) -> bool:
    """True if ``exc`` is an HTTP 409 (conflict / already exists)."""
    return isinstance(exc, ResourceExists) or _status_code(exc) == 409


def is_transient(exc: BaseException) -> bool:
    """True if ``exc`` is a transient 5xx the caller may retry."""
    if isinstance(exc, ApiTransientError):
        return True
    code = _status_code(exc)
    return code is not None and 500 <= code < 600


def raise_conflict_as_exists(
    exc: BaseException,
    *,
    resource: str,
    alias: Optional[str] = None,
    parent_path: Optional[str] = None,
) -> None:
    """Re-raise a 409 as :class:`ResourceExists` with folder/alias context.

    The v3 catalog enforces unique paths (``owner/folder/alias``), so a
    create can 409 on an alias collision even when ``overwrite=True`` has
    already freed the system name. The raw server message ("X already
    exist.") does not say which alias or folder collided; this rewrites it
    into something actionable.

    No-op if ``exc`` is not a 409 (the caller then re-raises the original).
    Requires ``exc`` to carry httpx ``request``/``response`` (every
    ``ApiClientError`` does); other 409-shaped errors are left untouched.

    Args:
        exc: The exception caught from a create/publish call.
        resource: Human label for what was being created, e.g.
            ``"layer 'john_doe.foo'"`` or ``"map 'john_doe.bar'"``.
        alias: The display alias passed to the create call, if any.
        parent_path: The target folder path, if any.
    """
    if not is_conflict(exc):
        return
    request = getattr(exc, "request", None)
    response = getattr(exc, "response", None)
    if request is None or response is None:
        return

    alias_part = f" with alias {alias!r}" if alias else ""
    where = f" in {parent_path!r}" if parent_path else ""
    raise ResourceExists(
        f"Cannot create {resource}{alias_part}{where}: a resource with the "
        f"same name or alias already exists there. Pick a different alias/name, "
        f"pass overwrite=True, or delete the existing resource first.",
        request=request,
        response=response,
    ) from exc


__all__ = [
    "ApiTransientError",
    "ResourceExists",
    "ResourceNotFound",
    "is_conflict",
    "is_not_found",
    "is_transient",
    "raise_conflict_as_exists",
]
