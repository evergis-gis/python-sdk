"""Create a catalog symlink (shortcut) to an existing resource.

``create_link`` resolves the ``target`` resource (by catalog path,
resource ID, or system name), then publishes a symlink under
``parent_path``. Symlinks are first-class catalog resources -
``resolve_resource`` on a symlink returns the link itself; follow
via ``targetResourceId`` if you need the underlying resource.

Re-runs reuse the same link (server returns 409 → idempotent).
"""

import os

from evergis_tools import Client, ResourceNotFound
from evergis_tools.catalog import create_link, delete_resource, resolve_resource


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")


with Client() as client:
    username = client.account.get_user_info().username
    target = f"{username}.{RESOURCE_PREFIX}_sandbox_polygon"
    parent = f"{username}/{PROJECT_PATH}/links"

    link_path = f"{parent}/{target}"
    try:
        existing = resolve_resource(client, link_path)
        delete_resource(client, existing.resourceId, cascade=True)
    except ResourceNotFound:
        pass

    link = create_link(
        client, target,
        parent_path=parent,
        description="Shortcut to the sandbox polygon seed layer",
        tags=["example", "symlink"],
        log=False,
    )
    print(f"+ link {parent}/{link.name}  → {target}  id={link.resourceId}")
