"""Batch-upload files from a local directory, filtering by extension.

``upload_files_by_extension`` walks the source directory, picks files
matching the given extensions and uploads them into the destination
catalog folder.

The example seeds three small ``.txt`` files in a temporary directory,
uploads only the ``.txt`` ones, then deletes the temp dir on exit.
"""

import os
import tempfile
from pathlib import Path

from evergis_tools import Client
from evergis_tools.catalog import (
    delete_resource,
    upload_files_by_extension,
)


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")


with Client() as client:
    username = client.account.get_user_info().username
    base = f"{username}/{PROJECT_PATH}/catalog/upload_files"

    # Refresh the namespace contents so re-runs are observable.
    for name in ("alpha.txt", "beta.txt", "gamma.txt"):
        delete_resource(client, f"{base}/{name}", missing_ok=True)

    with tempfile.TemporaryDirectory() as tmp:
        src = Path(tmp)
        (src / "alpha.txt").write_text("alpha\n")
        (src / "beta.txt").write_text("beta\n")
        (src / "gamma.txt").write_text("gamma\n")
        # Non-matching extension - should be ignored by the filter below.
        (src / "ignored.bin").write_bytes(b"\x00\x01")

        results = upload_files_by_extension(
            client=client,
            directory_path=src,
            extensions=["txt"],
            parent_path=base,
        )

    print(f"uploaded {len(results)} file(s):")
    for r in results:
        print(f"  {r.name}: id={r.resourceId[:8]}")
