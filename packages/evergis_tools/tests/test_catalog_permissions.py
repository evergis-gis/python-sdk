# -*- coding: utf-8 -*-
"""Tests for catalog/permissions.py -- permission management functions."""

import pytest
from unittest.mock import MagicMock, patch

from evergis_api.schemas import (
    AccessControlListDc,
    RolePermissionDc,
    Permissions,
)

from evergis_tools.catalog.permissions import (
    get_permissions,
    set_permissions,
    add_permission,
    remove_permission,
    _resolve_resource_id,
    _normalize_permission,
)


# =====================================================================
# Fixtures
# =====================================================================


@pytest.fixture
def mock_client():
    client = MagicMock()
    client.catalog.get_permissions.return_value = AccessControlListDc(
        data=[
            RolePermissionDc(role="admin", permissions=Permissions.READ_WRITE_CONFIGURE),
            RolePermissionDc(role="viewer", permissions=Permissions.READ),
        ]
    )
    client.catalog.set_permissions_1.return_value = True
    return client


# =====================================================================
# _resolve_resource_id
# =====================================================================


class TestResolveResourceId:
    """Tests for _resolve_resource_id()."""

    def test_resource_id_returned_directly(self):
        client = MagicMock()
        result = _resolve_resource_id(client, "abc123", None)
        assert result == "abc123"

    @patch("evergis_tools.catalog.permissions.resolve_resource")
    def test_resource_path_resolved(self, mock_resolve):
        client = MagicMock()
        mock_resolve.return_value = MagicMock(resourceId="resolved_id")
        result = _resolve_resource_id(client, None, "em:Projects/Layer")
        assert result == "resolved_id"
        mock_resolve.assert_called_once_with(client, "em:Projects/Layer")

    def test_both_raises(self):
        with pytest.raises(ValueError, match="not both"):
            _resolve_resource_id(MagicMock(), "id", "path")

    def test_neither_raises(self):
        with pytest.raises(ValueError, match="either"):
            _resolve_resource_id(MagicMock(), None, None)


# =====================================================================
# _normalize_permission
# =====================================================================


class TestNormalizePermission:
    """Tests for _normalize_permission()."""

    def test_enum_passthrough(self):
        assert _normalize_permission(Permissions.READ) == Permissions.READ

    def test_string_read(self):
        assert _normalize_permission("read") == Permissions.READ

    def test_string_read_write(self):
        assert _normalize_permission("read,write") == Permissions.READ_WRITE

    def test_string_none(self):
        assert _normalize_permission("none") == Permissions.NONE

    def test_invalid_raises(self):
        with pytest.raises(ValueError, match="Invalid permission"):
            _normalize_permission("superadmin")


# =====================================================================
# get_permissions
# =====================================================================


class TestGetPermissions:
    """Tests for get_permissions()."""

    def test_by_resource_id(self, mock_client):
        result = get_permissions(mock_client, resource_id="abc123", log=False)
        mock_client.catalog.get_permissions.assert_called_once_with("abc123")
        assert len(result.data) == 2

    @patch("evergis_tools.catalog.permissions.resolve_resource")
    def test_by_resource_path(self, mock_resolve, mock_client):
        mock_resolve.return_value = MagicMock(resourceId="resolved_id")
        get_permissions(mock_client, resource_path="em:Layer", log=False)
        mock_client.catalog.get_permissions.assert_called_once_with("resolved_id")


# =====================================================================
# set_permissions
# =====================================================================


class TestSetPermissions:
    """Tests for set_permissions()."""

    def test_sets_permissions(self, mock_client):
        result = set_permissions(
            mock_client,
            {"admin": "read,write,configure", "viewer": "read"},
            resource_id="abc123",
            log=False,
        )
        assert result is True
        mock_client.catalog.set_permissions_1.assert_called_once()
        call_args = mock_client.catalog.set_permissions_1.call_args
        assert call_args.kwargs["resourceId"] == "abc123"
        acl = call_args.kwargs["body"]
        assert len(acl.data) == 2

    def test_accepts_enum_values(self, mock_client):
        result = set_permissions(
            mock_client,
            {"admin": Permissions.READ_WRITE_CONFIGURE},
            resource_id="abc123",
            log=False,
        )
        assert result is True


# =====================================================================
# add_permission
# =====================================================================


class TestAddPermission:
    """Tests for add_permission()."""

    def test_update_existing_role(self, mock_client):
        result = add_permission(
            mock_client, "viewer", "read,write", resource_id="abc123", log=False
        )
        assert result is True
        call_args = mock_client.catalog.set_permissions_1.call_args
        acl = call_args.kwargs["body"]
        # Should still have 2 roles (admin + updated viewer)
        assert len(acl.data) == 2

    def test_add_new_role(self, mock_client):
        result = add_permission(
            mock_client, "editor", "read,write", resource_id="abc123", log=False
        )
        assert result is True
        call_args = mock_client.catalog.set_permissions_1.call_args
        acl = call_args.kwargs["body"]
        # Should have 3 roles now
        assert len(acl.data) == 3
        role_names = {entry.role for entry in acl.data}
        assert "editor" in role_names


# =====================================================================
# remove_permission
# =====================================================================


class TestRemovePermission:
    """Tests for remove_permission()."""

    def test_remove_existing_role(self, mock_client):
        result = remove_permission(
            mock_client, "viewer", resource_id="abc123", log=False
        )
        assert result is True
        call_args = mock_client.catalog.set_permissions_1.call_args
        acl = call_args.kwargs["body"]
        assert len(acl.data) == 1
        assert acl.data[0].role == "admin"

    def test_remove_nonexistent_role_raises(self, mock_client):
        with pytest.raises(ValueError, match="not found"):
            remove_permission(
                mock_client, "nonexistent", resource_id="abc123", log=False
            )
