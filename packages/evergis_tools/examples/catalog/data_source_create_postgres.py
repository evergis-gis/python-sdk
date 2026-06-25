"""Create a Postgres DataSource via the keyword helper.

``create_postgres_data_source`` builds a ``PostgresDataSourceDc``
from kwargs and delegates to ``create_data_source``. Same options
(``parent_path``, ``test``, ...) apply.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import create_postgres_data_source, delete_data_source


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")


with Client() as client:
    username = client.account.get_user_info().username
    name = f"{username}.{RESOURCE_PREFIX}_pg_kw"

    delete_data_source(client, name, missing_ok=True, log=False)

    create_postgres_data_source(
        client,
        name=name,
        alias="Postgres keyword example",
        description="Created via create_postgres_data_source(**kwargs)",
        tags=["example", "postgres"],
        host="db.example.com",
        port=5432,
        database="my_database",
        schema="public",
        user="my_user",
        test=True,
        password="my_password",
        parent_path=f"{username}/{PROJECT_PATH}/connections",
        log=False,
    )
    print(f"+ {name}")
