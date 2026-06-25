# -*- coding: utf-8 -*-
"""Create-point conflict handling: a 409 (or an overwrite=False pre-check)
surfaces as ``ResourceExists`` instead of a raw ``ApiClientError`` / ``ValueError``.
No network.
"""

from unittest.mock import MagicMock

import httpx
import pytest

from evergis_api import ApiClientError
from evergis_tools import ResourceExists
from evergis_tools.catalog import create_folder
from evergis_tools.account.roles import create_role
from evergis_tools.layers._utils import _handle_layer_overwrite


def _conflict() -> ApiClientError:
    req = httpx.Request("POST", "https://example/r")
    resp = httpx.Response(409, request=req, json={"ErrorType": "Duplicate"})
    return ApiClientError("HTTP 409", request=req, response=resp)


def _client_with_user():
    client = MagicMock()
    client.account.get_user_info.return_value = MagicMock(username="em")
    return client


class TestCreateFolderConflict:
    def test_409_becomes_resource_exists(self):
        client = _client_with_user()
        client.catalog.create_directory.side_effect = _conflict()
        with pytest.raises(ResourceExists) as info:
            create_folder(client, "Reports", parent_id="p1")
        assert "folder 'Reports'" in str(info.value)


class TestCreateRoleConflict:
    def test_409_becomes_resource_exists(self):
        client = MagicMock()
        client.account.create_role.side_effect = _conflict()
        with pytest.raises(ResourceExists) as info:
            create_role(client, "viewers", alias="Viewers")
        assert "role 'viewers'" in str(info.value)


class TestOverwritePreCheck:
    def test_existing_layer_raises_resource_exists(self):
        # overwrite=False + an existing Layer -> ResourceExists (was ValueError).
        client = MagicMock()
        layer_item = MagicMock(resourceId="id1")
        layer_item.type = "Layer"
        client.catalog.post_get_all.return_value = MagicMock(items=[layer_item])
        with pytest.raises(ResourceExists):
            _handle_layer_overwrite(
                client=client,
                layer_name="em.cities",
                create_table=True,
                overwrite=False,
                check_dependencies=False,
                strict_errors=True,
                log=False,
            )
