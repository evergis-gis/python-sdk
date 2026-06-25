"""Probe a DataSource connection without creating/updating.

``test_data_source`` runs the type-specific test endpoint
(``POST /ds/<type>/test-connection``) and returns ``True`` /
``False``. Spark and WMS have no test endpoint - call raises
``TypeError`` for those types.

This example uses fake credentials, so the call returns False;
swap in real credentials to see ``True``.
"""

from evergis_api.schemas import PostgresDataSourceDc

from evergis_tools import Client
from evergis_tools.catalog import test_data_source


with Client() as client:
    ds = PostgresDataSourceDc(
        name="ignored-by-test-endpoint",
        host="db.example.com",
        port=5432,
        database="my_database",
        schema="public",
        userName="my_user",
        password="my_password"
    )
    ok = test_data_source(client, ds)
    print(f"test_connection → {ok}")
    # Real-world: ok=True means the host accepts our credentials,
    # ok=False means it doesn't (wrong host / bad password / DNS).
