"""List every resource inside a catalog container via the paged generator.

``iter_resources(parent=...)`` works for any observable container -
``Directory``, ``Map``, ``Layer`` (children + attached files),
``TaskPrototype`` - the server filters by parent ID regardless of
parent type. See ``evergis_tools.catalog.folders.can_contain`` for the
exact containment rules per type.
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
    base = f"{username}/{PROJECT_PATH}/catalog/list"

    # Refresh seed children inside the namespace folder.
    for name in ("alpha", "beta", "gamma"):
        delete_resource(client, f"{base}/{name}", missing_ok=True)
        get_or_create_folder_by_path(client, f"{base}/{name}")

    print(f"contents of {base}:")
    for r in iter_resources(client, parent=base):
        print(f"  {r.name:20s} type={r.type}")
