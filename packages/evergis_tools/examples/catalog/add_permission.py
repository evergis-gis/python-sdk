"""Grant one role access to a resource without touching the rest.

``add_permission`` reads the current ACL, adds (or updates) the
named role, writes the merged ACL back. Other roles keep their
permissions.

Target: seed sandbox polygon (``evg_sandbox_polygon``).
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import add_permission, get_permissions


RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")


with Client() as client:
    username = client.account.get_user_info().username
    target = f"{username}.{RESOURCE_PREFIX}_sandbox_polygon"

    add_permission(
        client, role="Authenticated", permission="Read",
        resource_path=target, log=False,
    )
    acl = get_permissions(client, resource_path=target, log=False)
    print("ACL after add:")
    for entry in (acl.data or []):
        print(f"  {entry.role!r:20s} → {entry.permissions}")
