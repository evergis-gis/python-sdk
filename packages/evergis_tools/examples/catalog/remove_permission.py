"""Revoke one role's access without touching the rest.

``remove_permission`` reads the current ACL, drops the named role,
writes the trimmed ACL back. Raises ValueError if the role isn't
present.

Target: seed sandbox polygon (``evg_sandbox_polygon``). Re-run
after ``add_permission.py`` to see the role disappear.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import get_permissions, remove_permission


RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")


with Client() as client:
    username = client.account.get_user_info().username
    target = f"{username}.{RESOURCE_PREFIX}_sandbox_polygon"

    try:
        remove_permission(
            client, role="Authenticated",
            resource_path=target, log=False,
        )
        print(f"removed Authenticated from {target}")
    except ValueError as e:
        print(f"skip: {e}")

    acl = get_permissions(client, resource_path=target, log=False)
    print("ACL after remove:")
    for entry in (acl.data or []):
        print(f"  {entry.role!r:20s} → {entry.permissions}")
