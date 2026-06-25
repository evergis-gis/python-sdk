"""Cascade-delete a catalog resource, with optional missing_ok behaviour.

The wrapper resolves the identifier, then issues
``catalog.delete_resource(cascade=True)`` - the project rule for any
catalog deletion. ``missing_ok=True`` makes the call safe to re-run.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import delete_resource, get_or_create_folder_by_path


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")


with Client() as client:
    username = client.account.get_user_info().username
    base = f"{username}/{PROJECT_PATH}/catalog/delete"
    target = f"{base}/target"

    get_or_create_folder_by_path(client, target)

    print(f"first call:  deleted={delete_resource(client, target)}")
    print(
        f"second call: deleted="
        f"{delete_resource(client, target, missing_ok=True)}  (was missing)"
    )
