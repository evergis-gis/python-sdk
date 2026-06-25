"""Patch description / tags / icon on an existing catalog resource.

``update_resource_metadata`` is a partial update on top of
``patch_resource``. The server clears any field omitted from the body,
so the wrapper reads the current resource and only overrides the fields
you pass; the rest are carried along.

Argument semantics: ``None`` keeps the current value;
``""`` (description / icon) or ``[]`` (tags) clears.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import (
    delete_resource,
    get_or_create_folder_by_path,
    resolve_resource,
    update_resource_metadata,
)


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")


with Client() as client:
    username = client.account.get_user_info().username
    base = f"{username}/{PROJECT_PATH}/catalog/metadata"
    target = f"{base}/target"

    delete_resource(client, target, missing_ok=True)
    folder = get_or_create_folder_by_path(client, target)

    # 1. Initial set.
    update_resource_metadata(
        client, folder.resourceId,
        description="initial",
        tags=["alpha", "beta"],
    )
    fresh = resolve_resource(client, folder.resourceId)
    print(f"1) initial:    description={fresh.description!r}  tags={fresh.tags}")

    # 2. Change only description; tags survive.
    update_resource_metadata(client, folder.resourceId, description="updated")
    fresh = resolve_resource(client, folder.resourceId)
    print(f"2) desc only:  description={fresh.description!r}  tags={fresh.tags}")

    # 3. Clear tags explicitly.
    update_resource_metadata(client, folder.resourceId, tags=[])
    fresh = resolve_resource(client, folder.resourceId)
    print(f"3) tags=[]:    description={fresh.description!r}  tags={fresh.tags}")
