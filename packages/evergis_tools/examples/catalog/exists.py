"""Check resource existence by path / id (and system name).

``exists`` routes to the cheapest ``resource_exists_by_*_async`` server
endpoint based on the identifier shape. Use it instead of
``resolve_resource`` + try/except when you only need a yes/no answer.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import (
    delete_resource,
    exists,
    get_or_create_folder_by_path,
)


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")


with Client() as client:
    username = client.account.get_user_info().username
    base = f"{username}/{PROJECT_PATH}/catalog/exists"
    target = f"{base}/target"

    delete_resource(client, target, missing_ok=True)

    print(f"by path, before create: {exists(client, target)}")
    folder = get_or_create_folder_by_path(client, target)
    print(f"by path, after create:  {exists(client, target)}")
    print(f"by id:                  {exists(client, folder.resourceId)}")

    delete_resource(client, target)
