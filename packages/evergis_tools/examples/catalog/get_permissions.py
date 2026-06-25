"""Read the ACL (role → permission level) of a resource.

``get_permissions`` returns ``AccessControlListDc`` with one
``RolePermissionDc`` per role granted access. Each entry has a
``role`` (name) and a ``permissions`` string (e.g. ``"Read"``,
``"ReadWrite"``, ``"Full"``).

Uses the seed sandbox polygon (``evg_sandbox_polygon``) as the
target.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import get_permissions


RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")


with Client() as client:
    username = client.account.get_user_info().username
    target = f"{username}.{RESOURCE_PREFIX}_sandbox_polygon"

    acl = get_permissions(client, resource_path=target, log=False)
    print(f"ACL for {target}:")
    for entry in (acl.data or []):
        print(f"  {entry.role!r:20s} → {entry.permissions}")
