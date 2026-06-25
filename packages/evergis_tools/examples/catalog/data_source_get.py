"""Read a DataSource by name.

``get_data_source`` returns one of the ``*DataSourceInfoDc`` types
(Postgres / S3 / ArcGIS / WMS / MosRu / Spark) - fields depend on
the connection type.

Requires a DataSource called ``evg_ds_universal`` (created by
``data_source_create.py`` - that one runs without ``test=True``
and so always lands on the server).
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import get_data_source


RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")


with Client() as client:
    username = client.account.get_user_info().username
    name = f"{username}.{RESOURCE_PREFIX}_ds_universal"

    ds = get_data_source(client, name)
    print(f"name: {ds.name}")
    print(f"type: {ds.type}")
    print(f"alias: {ds.alias}")
    if getattr(ds, "host", None):
        print(f"host: {ds.host}:{ds.port}/{ds.database} (schema={ds.schema_})")
