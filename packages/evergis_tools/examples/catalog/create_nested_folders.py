"""Create a multi-level folder hierarchy in one call.

``get_or_create_folder_by_path`` walks the path from right to left
looking for the deepest existing parent, then creates whatever is
missing. Re-running is safe: existing folders are left untouched.

The example operates inside the pre-existing
``catalog/nested_folders/`` folder (declared in
``catalog_structure.yaml``); it creates levels inside and never
touches the namespace folder itself.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import (
    delete_resource,
    get_or_create_folder_by_path,
    iter_resources,
)


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")


with Client() as client:
    username = client.account.get_user_info().username
    base = f"{username}/{PROJECT_PATH}/catalog/nested_folders"

    # Clear leftovers inside the namespace from a previous run.
    delete_resource(client, f"{base}/level_1", missing_ok=True)

    # Three new levels in a single call - all intermediates are created.
    leaf = get_or_create_folder_by_path(
        client, f"{base}/level_1/level_2/level_3"
    )
    print(f"created leaf: {leaf.path}")

    # Verify each intermediate level exists as a folder.
    for level in (base, f"{base}/level_1", f"{base}/level_1/level_2"):
        children = [r.name for r in iter_resources(client, parent=level)]
        print(f"  {level}: {children}")
