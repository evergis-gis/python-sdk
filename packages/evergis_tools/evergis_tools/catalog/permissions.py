# -*- coding: utf-8 -*-
"""Permission management utilities for EverGIS resources."""

from typing import Dict, List, Optional, Union
import logging

from evergis_api import Client
from evergis_api.schemas import (
    AccessControlListDc,
    RolePermissionDc,
    Permissions,
)

from .resources import resolve_resource

logger = logging.getLogger(__name__)


def get_permissions(
    client: Client,
    *,
    resource_id: Optional[str] = None,
    resource_path: Optional[str] = None,
    log: bool = True,
) -> AccessControlListDc:
    """Get permissions (ACL) for a resource.

    Args:
        client: EverGIS API client
        resource_id: Resource ID (32 hex chars or UUID)
        resource_path: Resource path, system name, or catalog path
            (resolved via resolve_resource)
        log: Enable logging

    Returns:
        AccessControlListDc with current permissions

    Raises:
        ValueError: If neither resource_id nor resource_path is provided,
            or if resource cannot be resolved

    Example:
        >>> acl = get_permissions(client, resource_path="john_doe:Projects/MyLayer")
        >>> for entry in acl.data:
        ...     print(f"{entry.role}: {entry.permissions}")
    """
    resolved_id = _resolve_resource_id(client, resource_id, resource_path)

    if log:
        logger.info(f"Getting permissions for resource '{resolved_id}'")

    return client.catalog.get_permissions(resolved_id)


def set_permissions(
    client: Client,
    permissions: Dict[str, Union[str, Permissions]],
    *,
    resource_id: Optional[str] = None,
    resource_path: Optional[str] = None,
    log: bool = True,
) -> bool:
    """Set permissions (ACL) for a resource.

    Replaces all existing permissions with the provided ones.

    Args:
        client: EverGIS API client
        permissions: Dict mapping role names to permission levels.
            Values can be Permissions enum or strings:
            "read", "write", "configure", "read,write",
            "read,configure", "read,write,configure", "none"
        resource_id: Resource ID (32 hex chars or UUID)
        resource_path: Resource path, system name, or catalog path
            (resolved via resolve_resource)
        log: Enable logging

    Returns:
        True if permissions were set successfully

    Raises:
        ValueError: If neither resource_id nor resource_path is provided,
            or if resource cannot be resolved

    Example:
        >>> set_permissions(
        ...     client,
        ...     {"admin": "read,write,configure", "viewer": "read"},
        ...     resource_path="john_doe:Projects/MyLayer",
        ... )
    """
    resolved_id = _resolve_resource_id(client, resource_id, resource_path)

    acl = AccessControlListDc(
        data=[
            RolePermissionDc(
                role=role,
                permissions=_normalize_permission(perm),
            )
            for role, perm in permissions.items()
        ]
    )

    if log:
        roles_info = ", ".join(f"{r}={p}" for r, p in permissions.items())
        logger.info(f"Setting permissions for '{resolved_id}': {roles_info}")

    result = client.catalog.set_permissions_1(resourceId=resolved_id, body=acl)

    if log:
        logger.info(f"Permissions for '{resolved_id}' updated successfully")

    return result


def add_permission(
    client: Client,
    role: str,
    permission: Union[str, Permissions],
    *,
    resource_id: Optional[str] = None,
    resource_path: Optional[str] = None,
    log: bool = True,
) -> bool:
    """Add or update permission for a single role without affecting others.

    Args:
        client: EverGIS API client
        role: Role name to grant permission to
        permission: Permission level (string or Permissions enum)
        resource_id: Resource ID (32 hex chars or UUID)
        resource_path: Resource path, system name, or catalog path
        log: Enable logging

    Returns:
        True if permission was set successfully

    Example:
        >>> add_permission(
        ...     client, "editor", "read,write",
        ...     resource_path="john_doe:Projects/MyLayer",
        ... )
    """
    resolved_id = _resolve_resource_id(client, resource_id, resource_path)

    # Get current permissions
    current_acl = client.catalog.get_permissions(resolved_id)
    entries: List[RolePermissionDc] = list(current_acl.data or [])

    # Update or add role
    normalized = _normalize_permission(permission)
    found = False
    for entry in entries:
        if entry.role == role:
            entry.permissions = normalized
            found = True
            break

    if not found:
        entries.append(RolePermissionDc(role=role, permissions=normalized))

    new_acl = AccessControlListDc(data=entries)

    if log:
        logger.info(f"Setting permission for role '{role}' = '{normalized}' on '{resolved_id}'")

    result = client.catalog.set_permissions_1(resourceId=resolved_id, body=new_acl)

    if log:
        logger.info(f"Permission for role '{role}' on '{resolved_id}' updated successfully")

    return result


def remove_permission(
    client: Client,
    role: str,
    *,
    resource_id: Optional[str] = None,
    resource_path: Optional[str] = None,
    log: bool = True,
) -> bool:
    """Remove permission for a role from a resource.

    Args:
        client: EverGIS API client
        role: Role name to remove
        resource_id: Resource ID (32 hex chars or UUID)
        resource_path: Resource path, system name, or catalog path
        log: Enable logging

    Returns:
        True if permission was removed successfully

    Raises:
        ValueError: If role not found in current permissions

    Example:
        >>> remove_permission(client, "viewer", resource_path="john_doe:Projects/MyLayer")
    """
    resolved_id = _resolve_resource_id(client, resource_id, resource_path)

    # Get current permissions
    current_acl = client.catalog.get_permissions(resolved_id)
    entries: List[RolePermissionDc] = list(current_acl.data or [])

    new_entries = [e for e in entries if e.role != role]
    if len(new_entries) == len(entries):
        raise ValueError(f"Role '{role}' not found in permissions for resource '{resolved_id}'")

    new_acl = AccessControlListDc(data=new_entries)

    if log:
        logger.info(f"Removing permission for role '{role}' from '{resolved_id}'")

    result = client.catalog.set_permissions_1(resourceId=resolved_id, body=new_acl)

    if log:
        logger.info(f"Permission for role '{role}' removed from '{resolved_id}'")

    return result


# ---------------------------------------------------------------------------
# Internal helpers
# ---------------------------------------------------------------------------


def _resolve_resource_id(
    client: Client,
    resource_id: Optional[str],
    resource_path: Optional[str],
) -> str:
    """Resolve resource_id or resource_path to a resource ID string."""
    if resource_id and resource_path:
        raise ValueError("Provide either resource_id or resource_path, not both")
    if not resource_id and not resource_path:
        raise ValueError("Provide either resource_id or resource_path")

    if resource_id:
        return resource_id

    resource = resolve_resource(client, resource_path)
    return resource.resourceId


def _normalize_permission(value: Union[str, Permissions]) -> Permissions:
    """Convert string permission value to Permissions enum."""
    if isinstance(value, Permissions):
        return value
    # Try direct enum lookup by value
    try:
        return Permissions(value)
    except ValueError:
        valid = [p.value for p in Permissions]
        raise ValueError(
            f"Invalid permission '{value}'. Valid values: {valid}"
        )
