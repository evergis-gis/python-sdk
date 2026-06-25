"""Account helpers (auth, users, roles).

Thin orchestration on top of :mod:`evergis_api`'s ``AccountClient``.
The raw client is fine for one-off calls; this module covers the
multi-step flows that come up often (login + bearer wiring, paging
over large user lists, declarative role sync, user provisioning).
"""

from .auth import login_with_credentials
from .roles import create_role, iter_roles, update_role
from .users import iter_users, provision_user, set_roles, update_user

__all__ = [
    "create_role",
    "iter_roles",
    "iter_users",
    "login_with_credentials",
    "provision_user",
    "set_roles",
    "update_role",
    "update_user",
]
