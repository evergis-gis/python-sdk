"""Delete a DataSource by name.

Cleanup counterpart to ``create_*_data_source``. Removing the
DataSource doesn't touch layers / queries that reference it - they
will start failing once the connection is gone, so delete only
when nothing else points at the connection.

Removes the three example DataSources created by other examples
in this folder.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import delete_data_source


RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")


with Client() as client:
    username = client.account.get_user_info().username
    for short in ("ds_universal", "pg_kw", "s3_kw"):
        name = f"{username}.{RESOURCE_PREFIX}_{short}"
        removed = delete_data_source(client, name, missing_ok=True, log=False)
        print(f"{'-' if removed else '='} {name}")
