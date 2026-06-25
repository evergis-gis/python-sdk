"""Recursively upload a directory tree into the EverGIS catalog.

``upload_directory`` walks the source folder, mirrors its layout under
the destination catalog folder and applies default ignore patterns
(``__pycache__``, ``*.pyc``, ``.DS_Store``, ...). Pass ``rewrite=True``
to refresh files that already exist.

The example uses ``packages/evergis_tools/examples/demo_data/resources``
(a small tree with ``icons/``, ``images/``, ``map_icons/`` subfolders)
as the source.
"""

import os
from pathlib import Path

from evergis_tools import Client
from evergis_tools.catalog import delete_resource, upload_directory


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
REPO_ROOT = Path(__file__).resolve().parents[4]
LOCAL_DIR = REPO_ROOT / "packages/evergis_tools/examples/demo_data/resources"


with Client() as client:
    username = client.account.get_user_info().username
    base = f"{username}/{PROJECT_PATH}/catalog/upload_directory"

    # Refresh the namespace contents so re-runs are observable.
    for child in ("icons", "images", "map_icons"):
        delete_resource(client, f"{base}/{child}", missing_ok=True)

    results = upload_directory(
        client=client,
        directory_path=LOCAL_DIR,
        parent_path=base,
        rewrite=True,
    )

    print(f"uploaded {len(results)} file(s) from {LOCAL_DIR.name}/")
