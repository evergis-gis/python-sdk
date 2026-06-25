# -*- coding: utf-8 -*-
"""Tests for resolve_resource / exists not-found semantics (no network).

After the v3 typing pass, a missing resource raises ``ResourceNotFound``
(not a bare ``ValueError``), and a non-404 server failure (5xx / 403)
propagates as ``ApiClientError`` instead of being masked as "not found".
"""

from unittest.mock import MagicMock

import httpx
import pytest

from evergis_api import ApiClientError
from evergis_tools.catalog import resolve_resource, exists
from evergis_tools._errors import ResourceNotFound, is_not_found


def _api_error(status: int) -> ApiClientError:
    req = httpx.Request("GET", "https://example/resource")
    resp = httpx.Response(status, request=req)
    return ApiClientError(f"HTTP {status}", request=req, response=resp)


class TestResolveNotFound:
    def test_path_not_found_raises_resource_not_found(self):
        client = MagicMock()
        client.catalog.get_resource.side_effect = _api_error(404)
        with pytest.raises(ResourceNotFound):
            resolve_resource(client, "em/Folder/Missing")

    def test_id_not_found_raises_resource_not_found(self):
        client = MagicMock()
        client.catalog.get_resource.side_effect = _api_error(404)
        with pytest.raises(ResourceNotFound):
            resolve_resource(client, "efb02c4d89144f9792a94af22831f45d")

    def test_system_name_empty_raises_resource_not_found(self):
        client = MagicMock()
        client.catalog.post_get_all.return_value = MagicMock(items=[])
        with pytest.raises(ResourceNotFound):
            resolve_resource(client, "em.missing_layer")

    def test_5xx_propagates_as_apiclienterror_not_notfound(self):
        # A transient failure must NOT look like "not found".
        client = MagicMock()
        client.catalog.get_resource.side_effect = _api_error(503)
        with pytest.raises(ApiClientError) as info:
            resolve_resource(client, "em/Folder/Thing")
        assert not isinstance(info.value, ResourceNotFound)
        assert info.value.status_code == 503


class TestExists:
    def test_path_uses_exists_endpoint(self):
        # A catalog path goes through the cheap bool endpoint, not a full
        # resolve. The endpoint accepts a path for any resource type.
        client = MagicMock()
        client.catalog.resource_exists_by_id_async.return_value = True
        assert exists(client, "em/Folder/Thing") is True
        client.catalog.get_resource.assert_not_called()

    def test_path_false_when_absent(self):
        client = MagicMock()
        client.catalog.resource_exists_by_id_async.return_value = False
        assert exists(client, "em/Folder/Missing") is False

    def test_path_404_swallowed_to_false(self):
        client = MagicMock()
        client.catalog.resource_exists_by_id_async.side_effect = _api_error(404)
        assert exists(client, "em/Folder/Missing") is False

    def test_path_propagates_5xx(self):
        # exists() must not swallow a 5xx into False.
        client = MagicMock()
        client.catalog.resource_exists_by_id_async.side_effect = _api_error(500)
        with pytest.raises(ApiClientError):
            exists(client, "em/Folder/Thing")

    def test_system_name_uses_resolve(self):
        # A dotted system name can't use the exists endpoint - it resolves.
        client = MagicMock()
        client.catalog.post_get_all.return_value = MagicMock(items=[])
        assert exists(client, "em.missing_layer") is False
        client.catalog.resource_exists_by_id_async.assert_not_called()


class TestResourceNotFoundType:
    def test_message_only_construction(self):
        exc = ResourceNotFound("Resource not found by system name: 'em.x'")
        assert is_not_found(exc) is True
        assert exc.status_code == 404
        assert "em.x" in str(exc)

    def test_from_http_404_keeps_detail(self):
        exc = ResourceNotFound("not here", request=_api_error(404).request,
                               response=_api_error(404).response)
        assert is_not_found(exc) is True
        assert "not here" in str(exc)
