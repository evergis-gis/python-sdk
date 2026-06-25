"""Rename a resource and/or move it to a different parent.

``rename_resource`` picks the right server endpoint:

* ``new_name`` only -> ``patch_resource(name=...)`` (in-place rename).
* ``new_parent`` set (different from current) -> ``move_resource``;
  if ``new_name`` is also given, the rename is applied as a follow-up
  patch (the server's ``move`` ignores the new name field).
* ``new_parent`` equal to current -> falls back to a patch-rename
  (move would otherwise raise 409).

The example moves the ``test_file.png`` already uploaded by the init
pipeline into ``catalog/rename/`` between two pre-existing
folders (``folder_a``, ``folder_b``).

Prerequisite: run ``python -m evergis_tutorial_setup themes catalog --force`` first -
it creates ``catalog/rename/{folder_a,folder_b}`` and uploads
``test_file.png`` into ``catalog/rename/``.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import (
    delete_resource,
    exists,
    rename_resource,
    resolve_resource,
)


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")


with Client() as client:
    username = client.account.get_user_info().username
    base = f"{username}/{PROJECT_PATH}/catalog/rename"
    folder_a = f"{base}/folder_a"
    folder_b = f"{base}/folder_b"

    # Locate the test file. On a re-run after a half-finished round the
    # file may live in folder_a / folder_b instead of the base folder;
    # if leftovers exist in more than one place we keep the first match
    # and drop the rest so the renames below stay collision-free.
    candidates = (
        f"{base}/test_file.png",
        f"{folder_a}/test_file.png",
        f"{folder_b}/test_file.png",
    )
    existing = [p for p in candidates if exists(client, p)]
    if not existing:
        raise SystemExit(
            "test_file.png not found - run "
            "`python -m evergis_tutorial_setup themes catalog --force` first."
        )
    file_path = existing[0]
    for duplicate in existing[1:]:
        delete_resource(client, duplicate)

    fresh = resolve_resource(client, file_path)
    print(f"start:        parent={fresh.parentId[:8]}  name={fresh.name!r}")

    # 1. Move into folder_a.
    rename_resource(client, fresh.resourceId, new_parent=folder_a)
    fresh = resolve_resource(client, fresh.resourceId)
    print(f"-> folder_a:  parent={fresh.parentId[:8]}")

    # 2. Move into folder_b + rename.
    rename_resource(
        client, fresh.resourceId, new_name="moved.png", new_parent=folder_b
    )
    fresh = resolve_resource(client, fresh.resourceId)
    print(
        f"-> folder_b:  parent={fresh.parentId[:8]}  name={fresh.name!r}"
    )

    # 3. Rename in place (no parent change).
    rename_resource(client, fresh.resourceId, new_name="test_file.png")
    fresh = resolve_resource(client, fresh.resourceId)
    print(f"renamed back: parent={fresh.parentId[:8]}  name={fresh.name!r}")

    # 4. Move back to the starting folder so re-running the example
    #    starts from the same place every time.
    rename_resource(client, fresh.resourceId, new_parent=base)
    fresh = resolve_resource(client, fresh.resourceId)
    print(f"-> start:     parent={fresh.parentId[:8]}  name={fresh.name!r}")
