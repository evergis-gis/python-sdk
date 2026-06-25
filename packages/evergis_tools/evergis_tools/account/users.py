"""User management helpers."""

from __future__ import annotations

from typing import Iterable, Iterator, Optional

from typing import Any

from evergis_api import Client
from evergis_api.schemas import CreateUserDc, UpdateUserDc, UserInfoDc

from .._errors import raise_conflict_as_exists


_DEFAULT_PAGE_SIZE = 1000


def iter_users(
    client: Client,
    *,
    filter: Optional[str] = None,
    order_by: Optional[str] = None,
    users: Optional[list[str]] = None,
    roles: Optional[list[str]] = None,
    page_size: int = _DEFAULT_PAGE_SIZE,
) -> Iterator[UserInfoDc]:
    """Stream every user matching the filter, paging through the API.

    The server caps each ``get_users`` response - this generator
    automatically fetches subsequent pages until there are no more.

    Args:
        client: An authenticated ``evergis_api.Client``.
        filter: SQL-like filter for user name (``%`` and ``_`` wildcards).
        order_by: Server-side ordering property name.
        users: Restrict the list to specific usernames.
        roles: Restrict the list to users having any of these roles.
        page_size: Items per request (default 1000).

    Yields:
        ``UserInfoDc`` instances.
    """
    offset = 0
    while True:
        page = client.account.get_users(
            filter=filter,
            orderBy=order_by,
            offset=offset,
            limit=page_size,
            users=users,
            roles=roles,
        )
        items = list(page.items or [])
        for u in items:
            yield u
        if len(items) < page_size:
            return
        offset += page_size


def set_roles(
    client: Client,
    username: str,
    roles: Iterable[str],
) -> tuple[set[str], set[str]]:
    """Make ``username`` have **exactly** ``roles`` and nothing else.

    Reads the user's current role set, compares it to ``roles``, and
    issues ``add_to_role`` / ``remove_from_role`` only for the items
    that need to be added or removed.

    .. warning::
        This is strict equality - any role currently assigned but not
        in ``roles`` will be removed, including auto-managed system
        roles (typically those starting with ``__``). If you only want
        to grant a role, prefer ``client.account.add_to_role`` directly,
        or include the existing system roles in ``roles``.

    Args:
        client: An authenticated ``evergis_api.Client``.
        username: User to update.
        roles: Desired role set.

    Returns:
        ``(added, removed)`` for visibility.
    """
    target = set(roles)
    info = client.account.get_extended_user_info_1(username=username)
    current = set(info.roles or [])

    to_add = target - current
    to_remove = current - target

    for r in sorted(to_add):
        client.account.add_to_role(username=username, role=r)
    for r in sorted(to_remove):
        client.account.remove_from_role(username=username, role=r)

    return to_add, to_remove


def update_user(
    client: Client,
    username: str,
    **fields: Any,
) -> UserInfoDc:
    """Partial update for an existing user.

    The underlying ``account.update_user`` endpoint expects a full
    ``UpdateUserDc`` body - sending only the changed field would blank
    out the rest. This helper fetches the current state, overrides the
    provided ``fields``, and submits the merged body.

    Args:
        client: An authenticated ``evergis_api.Client``.
        username: User to update.
        **fields: Any field accepted by ``UpdateUserDc``: ``email``,
            ``first_name``, ``last_name``, ``patronymic``, ``phone``,
            ``company``, ``position``, ``location``, ``is_active``,
            ``is_email_confirmed``, ``is_subscribed``,
            ``is_open_last_project``, ``namespace``, ``emoji``,
            ``goals``, ``password``.

    Returns:
        ``UserInfoDc`` after the update.
    """
    current = client.account.get_extended_user_info_1(username=username)

    body_kwargs: dict[str, Any] = {"username": username}
    for name in UpdateUserDc.model_fields:
        if name == "username":
            continue
        if hasattr(current, name):
            body_kwargs[name] = getattr(current, name)
    body_kwargs.update(fields)

    client.account.update_user(body=UpdateUserDc(**body_kwargs))
    return client.account.get_user_info_1(username=username)


def provision_user(
    client: Client,
    username: str,
    password: str,
    email: str,
    *,
    first_name: str = "",
    last_name: str = "",
    roles: Optional[Iterable[str]] = None,
    with_namespace: bool = True,
    is_active: bool = True,
    is_email_confirmed: bool = True,
) -> UserInfoDc:
    """Onboard a user: create + (optional) namespace + add roles.

    Safe to re-run. If the user already exists, the function only
    reconciles roles (via :func:`set_roles`) and returns the existing
    record; other fields are left untouched.

    Args:
        client: An authenticated ``evergis_api.Client``.
        username: Login.
        password: Initial password.
        email: Contact email.
        first_name: Optional, for the user profile.
        last_name: Optional, for the user profile.
        roles: Roles to assign. ``None`` leaves role membership alone.
        with_namespace: Pass ``createNamespace=True`` to ``create_user``.
        is_active: Mark the new user as active.
        is_email_confirmed: Skip the email confirmation flow.

    Returns:
        ``UserInfoDc`` for the resulting user.
    """
    if client.account.is_username_exists(username=username):
        if roles is not None:
            set_roles(client, username, roles)
        return client.account.get_user_info_1(username=username)

    body = CreateUserDc(
        username=username,
        password=password,
        email=email,
        first_name=first_name,
        last_name=last_name,
        is_active=is_active,
        is_email_confirmed=is_email_confirmed,
    )
    # The is_username_exists pre-check above handles the common re-run, but a
    # lost race still 409s - translate it instead of leaking a raw error.
    try:
        client.account.create_user(
            body=body,
            sendConfirmEmail=False,
            createNamespace=with_namespace,
        )
    except Exception as e:
        raise_conflict_as_exists(e, resource=f"user {username!r}")
        raise

    if roles:
        for r in roles:
            client.account.add_to_role(username=username, role=r)

    return client.account.get_user_info_1(username=username)
