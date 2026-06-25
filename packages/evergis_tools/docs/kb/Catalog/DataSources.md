---
title: Catalog - Data Sources
module: evergis_tools.catalog
---

# Catalog - Data Sources

DataSource (DS) connection helpers: catalog resources backed by an external data
store (Postgres, S3, ArcGIS, WMS, MosRu, Spark). Create / update / test dispatch
to a per-type `POST /ds/<type>` endpoint by inspecting the DTO's class; get /
delete work on a flat, globally-unique name namespace.

Import: `from evergis_tools.catalog import ...`

Supported `*DataSourceDc` subclasses: `ArcGisDataSourceDc`, `PostgresDataSourceDc`,
`MosRuDataSourceDc`, `S3DataSourceDc`, `SparkDataSourceDc`, `WmsDataSourceDc`.
`SparkDataSourceDc` and `WmsDataSourceDc` have no test endpoint.

## Create / Update / Test

### create_data_source
Create a DataSource connection, dispatching to the per-type create endpoint.

```python
from evergis_api.schemas import PostgresDataSourceDc
from evergis_tools.catalog import create_data_source

create_data_source(
    client,
    PostgresDataSourceDc(name="john_doe.sales_db", host="db.example", database="sales"),
    parent_path="john_doe/EverGIS Resources/Connections",
    test=True,
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `ds` | required | Populated `*DataSourceDc` instance |
| `parent_id` | `None` | ID of the catalog folder to file the resource under |
| `parent_path` | `None` | Catalog folder path; auto-created if missing |
| `test` | `False` | Call the type's `test_connection` endpoint before creating |
| `log` | `True` | Enable logging |

**Returns:** `bool` - server response (`True` on success).

> **Warning:** `parent_id` and `parent_path` are mutually exclusive - passing both raises `ValueError`. Raises `ResourceExists` (importable from `evergis_tools`) if a data source with this name already exists (names are globally unique). See [[Errors]].

> **Note:** `test=True` is skipped for Spark / WMS (no test endpoint); a warning is logged and creation proceeds. When the test endpoint exists and the connection fails with a 403, the function raises `RuntimeError` carrying `ProviderCode` and `ExceptionMessage` from the response.

> **Note:** Raises `TypeError` when `ds` is not a known `DataSourceDc` subclass.

### update_data_source
Update an existing DataSource; the DTO's `name` selects the record on the server.

```python
from evergis_tools.catalog import update_data_source

ds.alias = "Renamed connection"
update_data_source(client, ds)
```

**Key params:** `client`, `ds` (the populated DTO), `log` (default `True`).

**Returns:** `bool` - server response.

> **Note:** Raises `TypeError` when `ds` is not a known `DataSourceDc` subclass.

### test_data_source
Probe the connection for `ds` without creating or updating it.

```python
from evergis_tools.catalog import test_data_source

if test_data_source(client, ds):
    create_data_source(client, ds)
```

**Key params:** `client`, `ds` (the populated DTO).

**Returns:** `bool` - `True` when the server confirms the connection works, `False` when it answers with `DataSourceConnectionFailed` (403; wrong credentials, host unreachable, etc.).

> **Note:** Errors other than 403 (auth, 5xx, missing endpoint) propagate as-is. Raises `TypeError` for Spark / WMS, which have no test endpoint.

## Read / Delete

### get_data_source
Read a DataSource by name.

```python
from evergis_tools.catalog import get_data_source

info = get_data_source(client, "john_doe.sales_db")
```

**Key params:** `client`, `name`.

**Returns:** A union of `*DataSourceInfoDc` (the matching type's info DTO).

### delete_data_source
Remove a DataSource by name.

```python
from evergis_tools.catalog import delete_data_source

removed = delete_data_source(client, "john_doe.sales_db", missing_ok=True)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `name` | required | Full DataSource system name (`"<user>.<short>"`) |
| `missing_ok` | `False` | When True, a 404 is swallowed and the function returns `False` instead of raising |
| `log` | `True` | Enable logging |

**Returns:** `bool` - `True` if the resource was present and removed; `False` if it did not exist (only with `missing_ok=True`).

> **Note:** The raw `DELETE /ds/<name>` response is unreliable (the server returns `False` even on success), so the result is inferred from the HTTP status.

## Keyword Helpers

### create_postgres_data_source
Convenience over `create_data_source` for Postgres.

```python
from evergis_tools.catalog import create_postgres_data_source

create_postgres_data_source(
    client,
    name="john_doe.sales_db", host="db.example", database="sales",
    user="reader", password="...", schema="public", test=True,
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `name` | required | DataSource system name |
| `host` | required | Postgres host |
| `database` | required | Database name |
| `user` | required | Login (maps to `userName`) |
| `password` | required | Password |
| `port` | `5432` | Postgres port |
| `schema` | `"public"` | Schema name |
| `alias` | `None` | Display alias |
| `description` | `None` | Description |
| `tags` | `None` | List of tags |
| `parent_id` | `None` | Catalog folder ID |
| `parent_path` | `None` | Catalog folder path; auto-created if missing |
| `test` | `False` | Test the connection before creating |
| `log` | `True` | Enable logging |

**Returns:** `bool` - server response (`True` on success).

### create_s3_data_source
Convenience over `create_data_source` for S3.

```python
from evergis_tools.catalog import create_s3_data_source

create_s3_data_source(
    client,
    name="john_doe.s3_ds", endpoint="s3.example.com",
    access_key="...", secret_key="...", region="ru-central1", test=True,
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `name` | required | DataSource system name |
| `endpoint` | required | S3 endpoint |
| `access_key` | required | Access key (maps to `accessKey`) |
| `secret_key` | required | Secret key (maps to `secretKey`) |
| `region` | `None` | S3 region |
| `port` | `None` | Endpoint port |
| `alias` | `None` | Display alias |
| `description` | `None` | Description |
| `tags` | `None` | List of tags |
| `parent_id` | `None` | Catalog folder ID |
| `parent_path` | `None` | Catalog folder path; auto-created if missing |
| `test` | `False` | Test the connection before creating |
| `log` | `True` | Enable logging |

**Returns:** `bool` - server response (`True` on success).

## See Also
- [[Catalog/Catalog|Catalog]]
