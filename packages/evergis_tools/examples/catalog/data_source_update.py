"""Update an existing DataSource.

Read the current record via ``get_data_source``, tweak fields,
push back with ``update_data_source``. The DTO's ``name`` selects
the record; other fields replace their counterparts.

Requires ``evg_ds_universal`` from ``data_source_create.py``.
"""

import os

from evergis_api.schemas import PostgresDataSourceDc, DataSourceType

from evergis_tools import Client
from evergis_tools.catalog import get_data_source, update_data_source


RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")


with Client() as client:
    username = client.account.get_user_info().username
    name = f"{username}.{RESOURCE_PREFIX}_ds_universal"

    current = get_data_source(client, name)
    print(f"before: alias={current.alias!r}  host={current.host}:{current.port}")

    # Rebuild the DTO (server expects all fields the type carries).
    ds = PostgresDataSourceDc(
        name=name,
        alias="Postgres (updated)",
        description=current.description,
        tags=list(current.tags) if current.tags else None,
        host=current.host,
        port=5433,                       # ← changed
        database=current.database,
        schema=current.schema_,
        userName=current.userName,
        password="rotated-not-a-real-password",
        type=DataSourceType.POSTGRES,
    )
    update_data_source(client, ds, log=False)

    updated = get_data_source(client, name)
    print(f"after:  alias={updated.alias!r}  host={updated.host}:{updated.port}")
