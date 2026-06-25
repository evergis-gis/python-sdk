"""Upload a single file from disk into the EverGIS catalog.

``upload_file`` resolves the destination folder (catalog path or
resource ID), creates missing folders along the way, and uploads the
file's bytes. Use this for files already on disk; for content built at
runtime see ``create_file``.
"""

import os
from pathlib import Path

from evergis_tools import Client
from evergis_tools.catalog import delete_resource, upload_file


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
REPO_ROOT = Path(__file__).resolve().parents[4]
LOCAL_FILE = REPO_ROOT / (
    "packages/evergis_tools/examples/demo_data/catalog/rename/test_file.png"
)


with Client() as client:
    username = client.account.get_user_info().username
    base = f"{username}/{PROJECT_PATH}/catalog/upload_file"
    catalog_path = f"{base}/{LOCAL_FILE.name}"

    # Start clean so re-runs are observable.
    delete_resource(client, catalog_path, missing_ok=True)

    result = upload_file(
        client=client,
        file_path=LOCAL_FILE,
        parent_path=base,
    )
    print(f"uploaded {result.name}: id={result.resourceId[:8]}  size={result.size}")
