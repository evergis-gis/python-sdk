"""Replace the entire ACL of a resource in one shot.

``set_permissions`` takes a ``{role: permission}`` dict and writes
it as the **complete** ACL - roles not in the dict lose access.
Use ``add_permission`` / ``remove_permission`` for incremental
changes.

Target: seed sandbox polygon (``evg_sandbox_polygon``).
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import set_permissions


RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")


with Client() as client:
    username = client.account.get_user_info().username
    target = f"{username}.{RESOURCE_PREFIX}_sandbox_polygon"

    # Wipe + set - only the listed roles will have access afterwards.
    # ``Authenticated`` is a built-in role for any logged-in user.
    set_permissions(
        client,
        permissions={"Authenticated": "Read"},
        resource_path=target,
        log=False,
    )
    print(f"set ACL for {target}: Authenticated=Read")
