"""Role helpers."""

from __future__ import annotations

from typing import Any, Iterator, Optional

from evergis_api import Client
from evergis_api.schemas import CreateRoleDc, RoleInfoDc, UpdateRoleDc

from .._errors import raise_conflict_as_exists


_DEFAULT_PAGE_SIZE = 1000


def iter_roles(
    client: Client,
    *,
    filter: Optional[str] = None,
    user_filter: Optional[str] = None,
    order_by: Optional[str] = None,
    with_system: Optional[bool] = None,
    page_size: int = _DEFAULT_PAGE_SIZE,
) -> Iterator[RoleInfoDc]:
    """Stream every role matching the filter, paging through the API.

    The server caps each ``get_roles`` response - this generator
    automatically fetches subsequent pages until there are no more.

    Args:
        client: An authenticated ``evergis_api.Client``.
        filter: SQL-like filter for role name (``%`` and ``_`` wildcards).
        user_filter: SQL-like filter to restrict roles to those whose
            members match the given user-name pattern.
        order_by: Server-side ordering property name.
        with_system: Include built-in/system roles.
        page_size: Items per request (default 1000).

    Yields:
        ``RoleInfoDc`` instances.
    """
    offset = 0
    while True:
        page = client.account.get_roles(
            filter=filter,
            userFilter=user_filter,
            orderBy=order_by,
            withSystem=with_system,
            offset=offset,
            limit=page_size,
        )
        items = list(page.items or [])
        for r in items:
            yield r
        if len(items) < page_size:
            return
        offset += page_size


def _find_role(client: Client, name: str) -> Optional[RoleInfoDc]:
    """Look up a single role by exact name.

    The server's ``filter`` is a substring/wildcard match, so it can return
    several roles; we keep only the exact-name one.
    """
    for r in iter_roles(client, filter=name, with_system=True):
        if r.name == name:
            return r
    return None


def create_role(
    client: Client,
    name: str,
    *,
    alias: Optional[str] = None,
    description: Optional[str] = None,
) -> RoleInfoDc:
    """Create a new role.

    Args:
        client: An authenticated ``evergis_api.Client``.
        name: System name (the value passed to ``add_to_role``).
        alias: Human-readable label.
        description: Free-form description.

    Returns:
        ``RoleInfoDc`` for the created role.

    Raises:
        ResourceExists: if a role with this name already exists.
    """
    try:
        client.account.create_role(
            body=CreateRoleDc(name=name, alias=alias, description=description)
        )
    except Exception as e:
        raise_conflict_as_exists(e, resource=f"role {name!r}", alias=alias)
        raise
    found = _find_role(client, name)
    if found is None:
        raise RuntimeError(f"role {name!r} not found after create")
    return found


def update_role(
    client: Client,
    name: str,
    **fields: Any,
) -> RoleInfoDc:
    """Partial update for an existing role.

    The underlying ``account.update_role`` endpoint takes a full
    ``UpdateRoleDc`` body. This helper looks up the current role to
    preserve ``alias``, then submits the merged body.

    .. note::
        ``description`` is not returned by the role-listing endpoint,
        so it cannot be auto-preserved. Pass ``description=`` explicitly
        if you want to set or change it.

    Args:
        client: An authenticated ``evergis_api.Client``.
        name: Current name of the role to update.
        **fields: Any field accepted by ``UpdateRoleDc``: ``name``
            (rename), ``alias``, ``description``.

    Returns:
        ``RoleInfoDc`` for the updated role.

    Raises:
        ValueError: if no role with the given name exists.
    """
    current = _find_role(client, name)
    if current is None:
        raise ValueError(f"role {name!r} not found")

    body_kwargs: dict[str, Any] = {
        "old_name": name,
        "name": current.name,
        "alias": current.alias,
    }
    body_kwargs.update(fields)
    client.account.update_role(body=UpdateRoleDc(**body_kwargs))

    new_name = body_kwargs["name"]
    found = _find_role(client, new_name)
    if found is None:
        raise RuntimeError(
            f"role {new_name!r} disappeared after update"
        )
    return found
