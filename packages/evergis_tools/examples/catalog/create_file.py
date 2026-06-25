"""Create and update a catalog file from in-memory content.

* ``create_file`` - new file from ``str`` / ``bytes``. Errors if a file
  with the same name already exists at the destination (use
  ``update_file`` to overwrite).
* ``update_file`` - rewrite an existing file's content.

Use these when the body is built at runtime (a rendered template, a
small generated script, query output, ...). For files that already
live on disk use ``upload_file``.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import (
    create_file,
    delete_resource,
    resolve_resource,
    update_file,
)


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")


SCRIPT_V1 = """\
# Tutorial demo - version 1.
print("hello from create_file")
"""

SCRIPT_V2 = """\
# Tutorial demo - version 2 (after update_file).
print("hello from update_file")
print("now with two lines")
"""


with Client() as client:
    username = client.account.get_user_info().username
    folder_path = f"{username}/{PROJECT_PATH}/catalog/create_file"
    file_path = f"{folder_path}/hello.py"

    # Start clean so re-running the example works.
    delete_resource(client, file_path, missing_ok=True)

    # 1. Create from in-memory content.
    create_file(
        client,
        name="hello.py",
        content=SCRIPT_V1,
        parent_path=folder_path,
        description="Tutorial demo script",
    )
    fresh = resolve_resource(client, file_path)
    print(f"created: size={fresh.size} bytes  description={fresh.description!r}")

    # 2. Overwrite the file with new content.
    update_file(client, file_path, SCRIPT_V2)
    fresh = resolve_resource(client, file_path)
    print(f"updated: size={fresh.size} bytes")
