# -*- coding: utf-8 -*-
"""Tests for ``evergis_tools._errors``.

Covers the two faces of the module:

* Predicates against raw ``ApiClientError`` (no subclassing) - that's
  the common case because the autogen client raises plain
  ``ApiClientError`` with ``status_code``.
* Predicates against the typed subclasses, for wrappers that opted
  into the classification themselves.
"""

from __future__ import annotations

import httpx
import pytest

from evergis_api._generated.exceptions import ApiClientError
from evergis_tools._errors import (
    ApiTransientError,
    ResourceExists,
    ResourceNotFound,
    is_conflict,
    is_not_found,
    is_transient,
    raise_conflict_as_exists,
)


def _make_exc(cls, status_code: int) -> ApiClientError:
    """Build an exception with a real httpx request/response so
    ``status_code`` populates the same way as in production."""
    req = httpx.Request("GET", "https://example/test")
    resp = httpx.Response(status_code, request=req)
    return cls(f"HTTP {status_code}", request=req, response=resp)


class TestPredicatesOnApiClientError:
    """Plain ApiClientError - the common case from the autogen client."""

    @pytest.mark.parametrize("code, expected_predicate", [
        (404, is_not_found),
        (409, is_conflict),
        (500, is_transient),
        (503, is_transient),
    ])
    def test_matches(self, code, expected_predicate):
        exc = _make_exc(ApiClientError, code)
        assert expected_predicate(exc) is True

    @pytest.mark.parametrize("code", [200, 301, 400, 401, 403, 422])
    def test_no_false_positives(self, code):
        exc = _make_exc(ApiClientError, code)
        assert is_not_found(exc) is False
        assert is_conflict(exc) is False
        assert is_transient(exc) is False

    def test_non_api_exception_returns_false(self):
        exc = ValueError("nothing to do with HTTP")
        assert is_not_found(exc) is False
        assert is_conflict(exc) is False
        assert is_transient(exc) is False


class TestPredicatesOnSubclasses:
    """When a wrapper raised the typed subclass, predicates still match."""

    def test_resource_not_found(self):
        exc = _make_exc(ResourceNotFound, 404)
        assert is_not_found(exc) is True
        assert is_conflict(exc) is False

    def test_resource_exists(self):
        exc = _make_exc(ResourceExists, 409)
        assert is_conflict(exc) is True
        assert is_not_found(exc) is False

    def test_transient(self):
        exc = _make_exc(ApiTransientError, 502)
        assert is_transient(exc) is True


class TestIsinstanceCompatibility:
    """Subclasses must keep ``except ApiClientError`` blocks working."""

    @pytest.mark.parametrize("cls", [
        ResourceNotFound, ResourceExists, ApiTransientError,
    ])
    def test_subclass_is_api_client_error(self, cls):
        assert issubclass(cls, ApiClientError)


class TestRaiseConflictAsExists:
    """Translation of a raw 409 into a contextual ResourceExists."""

    def test_409_reraised_as_resource_exists_with_context(self):
        exc = _make_exc(ApiClientError, 409)
        with pytest.raises(ResourceExists) as info:
            raise_conflict_as_exists(
                exc,
                resource="layer 'em.foo'",
                alias="My Layer",
                parent_path="em/Projects/Data",
            )
        msg = str(info.value)
        assert "layer 'em.foo'" in msg
        assert "My Layer" in msg
        assert "em/Projects/Data" in msg
        # original error is chained for debugging
        assert info.value.__cause__ is exc
        # request/response carried over -> status_code stays 409
        assert info.value.status_code == 409

    def test_message_without_optional_context(self):
        exc = _make_exc(ApiClientError, 409)
        with pytest.raises(ResourceExists) as info:
            raise_conflict_as_exists(exc, resource="map 'em.bar'")
        msg = str(info.value)
        assert "map 'em.bar'" in msg
        # no stray "with alias" / "in" fragments when not provided
        assert "alias" not in msg.split(":")[0]

    @pytest.mark.parametrize("code", [200, 400, 404, 500])
    def test_non_conflict_is_noop(self, code):
        exc = _make_exc(ApiClientError, code)
        # returns None and does NOT raise -> caller re-raises original
        assert raise_conflict_as_exists(exc, resource="layer 'x'") is None

    def test_409_without_request_response_is_noop(self):
        class FakeConflict(Exception):
            status_code = 409

        exc = FakeConflict("already exist")
        assert is_conflict(exc) is True
        # no httpx request/response to carry -> leave it for the caller
        assert raise_conflict_as_exists(exc, resource="layer 'x'") is None
