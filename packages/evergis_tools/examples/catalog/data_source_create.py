"""Create a DataSource via the universal ``create_data_source``.

Takes any ``*DataSourceDc`` subclass and dispatches to the matching
``POST /ds/<type>`` endpoint based on its class. Use the keyword
helpers (``create_postgres_data_source`` / ``create_s3_data_source``)
when the DTO would just wrap kwargs; reach for ``create_data_source``
when you need an exotic type (ArcGIS / WMS / MosRu / Spark).
"""

import os

from evergis_api.schemas import PostgresDataSourceDc, DataSourceType

from evergis_tools import Client
from evergis_tools.catalog import create_data_source, delete_data_source


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")


with Client() as client:
    username = client.account.get_user_info().username
    name = f"{username}.{RESOURCE_PREFIX}_ds_universal"

    delete_data_source(client, name, missing_ok=True, log=False)

    ds = PostgresDataSourceDc(
        name=name,
        alias="Universal create example",
        description="Created via create_data_source(ds_dto)",
        tags=["example"],
        host="db.example.test",
        port=5432,
        database="example",
        schema="public",
        userName="reader",
        password="not-a-real-password",
        type=DataSourceType.POSTGRES,
    )
    create_data_source(
        client, ds,
        parent_path=f"{username}/{PROJECT_PATH}/connections",
        log=False,
    )
    print(f"+ {name}")
