"""Create an S3 DataSource via the keyword helper.

``create_s3_data_source`` builds an ``S3DataSourceDc`` from kwargs.
S3 connections are typically used as the ``source_url`` for
bulk-import workers (CSV/GPKG/Shapefile coming from object storage).
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import create_s3_data_source, delete_data_source


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")


with Client() as client:
    username = client.account.get_user_info().username
    name = f"{username}.{RESOURCE_PREFIX}_s3_kw"

    delete_data_source(client, name, missing_ok=True, log=False)

    create_s3_data_source(
        client,
        name=name,
        alias="S3 keyword example",
        description="Created via create_s3_data_source(**kwargs)",
        tags=["example", "s3"],
        endpoint="https://s3.example.test",
        region="ru-central1",
        access_key="AKIAEXAMPLE",
        secret_key="not-a-real-secret",
        parent_path=f"{username}/{PROJECT_PATH}/connections",
        log=False,
    )
    print(f"+ {name}")
