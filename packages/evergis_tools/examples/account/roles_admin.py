"""Role admin lifecycle: create, partial update, list, remove.

* ``create_role`` / ``update_role`` - wrappers; the underlying API
  takes a full ``UpdateRoleDc`` body, so the update wrapper loads the
  current role and submits the merged body.
* ``remove_role`` - direct ``client.account.remove_role`` (one call,
  no body).
"""

from evergis_tools import Client
from evergis_tools.account import create_role, iter_roles, update_role


DEMO_ROLE = "evg_demo_role"


with Client() as client:
    # Cleanup leftover from a previous failed run, if any.
    if any(r.name == DEMO_ROLE for r in iter_roles(client, filter=DEMO_ROLE)):
        client.account.remove_role(rolename=DEMO_ROLE)
        print(f"removed leftover {DEMO_ROLE}")

    # 1. Create.
    role = create_role(
        client,
        DEMO_ROLE,
        alias="EverGIS demo role",
        description="Created by examples/account/roles_admin.py",
    )
    print(f"created: {role.name}")

    # 2. Partial update - only the changed field is passed.
    updated = update_role(
        client, DEMO_ROLE, alias="EverGIS demo role (updated alias)"
    )
    print(f"updated: alias={updated.alias!r}")

    # 3. List custom roles (system roles excluded).
    print("custom roles:")
    for r in iter_roles(client, with_system=False):
        marker = "  <-- demo" if r.name == DEMO_ROLE else ""
        print(f"  {r.name:30s} alias={(r.alias or ''):30s}{marker}")

    # 4. Remove.
    client.account.remove_role(rolename=DEMO_ROLE)
    print(f"removed: {DEMO_ROLE}")
