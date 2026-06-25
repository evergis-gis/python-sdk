---
title: EQL
module: evergis_tools.eql
---

# EQL

Execute EQL queries with automatic chunked loading. Import: `from evergis_tools.eql import ...`

## eql_query_to_geodataframe
Execute EQL query, return GeoDataFrame with geometry.

```python
from evergis_tools.eql import eql_query_to_geodataframe

gdf = eql_query_to_geodataframe(
    query="SELECT * FROM john_doe.cities WHERE population > @min_pop",
    client=client,
    chunk_size=1000,
    parameters={"@min_pop": 100000},
)
```

**Key params:** `query`, `client`, `chunk_size=1000`, `columns`, `ds`, `geometry_field="geometry"`, `id_field`, `parameters`, `with_geom=True`, `target_crs`

> **Tip:** pass `geometry_field="auto"` when the geometry column name
> is unknown (`geometry` vs `geom`). The wrapper runs one
> `/eql/description` call (independent of result size) and uses
> whichever column is the geometry one, falling back to `"geometry"` if
> detection fails.

## eql_query_to_dataframe
Execute EQL query, return pandas DataFrame (no geometry). For aggregates, counts, tabular data.

```python
from evergis_tools.eql import eql_query_to_dataframe

df = eql_query_to_dataframe(
    query="SELECT count(*) as cnt FROM john_doe.cities",
    client=client,
)
```

**Key params:** same as geodataframe version, minus `geometry_field`, `with_geom`, `target_crs`

## eql_describe
Describe a query's output columns without fetching any rows. Thin
wrapper over `POST /eql/description`. Use it to validate a query, list
its columns and types, or find the geometry field before fetching.

```python
from evergis_tools.eql import eql_describe

for col in eql_describe("SELECT * FROM john_doe.cities", client):
    print(col["name"], col["type"], col["kind"], col["is_geometry"])
```

Returns one dict per output column:

| Key | Description |
|-----|-------------|
| `name` | column name |
| `type` | value type (`"String"`, `"Int64"`, ...); for the geometry column the geometry type (`"Point"`, ...) |
| `kind` | `"geometry"` / `"string"` / `"calculated"` / `"attribute"` |
| `is_geometry` | `True` for the geometry column |

**Key params:** `query`, `client`, `ds`, `parameters`

This is what `geometry_field="auto"` (above) uses under the hood.

## Parameters
Both functions support `@` parameters for safe EQL injection:

```python
gdf = eql_query_to_geodataframe(
    query="SELECT * FROM john_doe.table WHERE status = @status AND year > @year",
    client=client,
    parameters={"@status": "active", "@year": 2020},
)
```

## Async Versions
```python
from evergis_tools._async.eql import (
    eql_describe,
    eql_query_to_dataframe,
    eql_query_to_geodataframe,
)

df = await eql_query_to_dataframe(query, async_client)
gdf = await eql_query_to_geodataframe(query, async_client)
cols = await eql_describe(query, async_client)
```

## See Also
- [[GeoDataFrames]] - Convert features to/from GeoDataFrame
- [[Async]]
