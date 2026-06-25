"""Extract a zip archive that lives in the catalog into another folder.

``extract_zip`` resolves the archive and target folder, then calls
``catalog.extract_zip_archive``. ``conflict_strategy`` controls what
happens to existing entries at the target: ``Skip`` (default),
``Overwrite``, ``GenerateUnique``, ``ThrowError``.

Source: ``german_lands.zip`` from the shared sample-data catalog owned
by ``SAMPLE_DATA_OWNER`` (default ``edu``), read-only here. Extracted
entries land in the caller's own ``catalog/extract`` folder.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import (
    delete_resource,
    extract_zip,
    get_or_create_folder_by_path,
    iter_resources,
)


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")


with Client() as client:
    username = client.account.get_user_info().username
    archive = (
        f"{SAMPLE_DATA_OWNER}/EverGIS Sample Data Catalog/Source files - raw archives"
        "/Source files - Shapefile/german_lands.zip"
    )
    target = f"{username}/{PROJECT_PATH}/catalog/extract"

    # Start with an empty target so re-runs show only this run's output.
    delete_resource(client, target, missing_ok=True)
    get_or_create_folder_by_path(client, target)

    extract_zip(
        client,
        archive,
        target_parent=target,
        conflict_strategy="Overwrite",
    )

    print(f"contents of {target}:")
    for r in iter_resources(client, parent=target):
        print(f"  {r.name:25s}  type={r.type}")
