---
title: Features
module: evergis_tools.features
---

# Features

Add, edit, query, and convert layer features. Import: `from evergis_tools.features import ...`

---

## Add Features

### add_gdf_features_to_layer
Add GeoDataFrame features to existing layer with size-based chunking.

```python
from evergis_tools.features import add_gdf_features_to_layer

results = add_gdf_features_to_layer(
    client, gdf, "john_doe.my_layer",
    target_sr=4326,
    geometry_type="MultiPolygon",
    log=True,
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `gdf` | required | GeoDataFrame with data |
| `layer_name` | `None` | Layer system name |
| `layer_path` | `None` | Catalog path / resource ID (alternative to `layer_name`) |
| `target_sr` | `3857` | Target coordinate system |
| `geometry_type` | `None` | Filter by geometry type |
| `chunk_size_bytes` | `1_200_000` | Max chunk size in bytes |
| `allow_additional_attributes` | `True` | Accept fields not in layer schema |
| `log` | `False` | Enable logging |

**Returns:** `List[LayerUpdateInfoDc]` - one result per chunk with `createdIds`.

> **Warning:** `target_sr` default is **3857** (Web Mercator). If your layer uses 4326 (WGS84), pass `target_sr=4326` explicitly.

### add_df_features_to_layer
Add pandas DataFrame features to non-spatial table (no geometry).

```python
from evergis_tools.features import add_df_features_to_layer

results = add_df_features_to_layer(client, df, "john_doe.my_table", log=True)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `df` | required | pandas DataFrame |
| `layer_name` | `None` | Layer/table system name |
| `layer_path` | `None` | Catalog path (alternative) |
| `chunk_size_bytes` | `1_200_000` | Max chunk size |
| `allow_additional_attributes` | `True` | Accept extra fields |
| `log` | `False` | Enable logging |

**Returns:** `List[LayerUpdateInfoDc]`

---

## Edit Features

### edit_layer_by_gdf
Update existing features in a layer from GeoDataFrame. Requires ID column.

```python
from evergis_tools.features import edit_layer_by_gdf

results = edit_layer_by_gdf(client, gdf, "john_doe.my_layer", id_column="gid")
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `gdf` | required | GeoDataFrame with updated data |
| `layer_name` | `None` | Layer system name |
| `layer_path` | `None` | Catalog path (alternative) |
| `target_sr` | `3857` | Target coordinate system |
| `geometry_type` | `None` | Filter by geometry type |
| `id_column` | `"id"` | Column with feature IDs (must be string) |
| `chunk_size_bytes` | `5_000_000` | Max chunk size |
| `log` | `True` | Enable logging |

**Returns:** `List` - update results per chunk.

> **Note:** Update API does NOT support `allowAdditionalAttributes`. Fields not in layer schema are silently filtered out.

### edit_layer_by_df
Update existing features from DataFrame (no geometry).

```python
from evergis_tools.features import edit_layer_by_df

results = edit_layer_by_df(client, df, "john_doe.my_table", id_column="gid")
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `df` | required | pandas DataFrame with updated data |
| `layer_name` | `None` | Layer/table system name |
| `layer_path` | `None` | Catalog path (alternative) |
| `id_column` | `"id"` | Column with feature IDs |
| `chunk_size_bytes` | `1_200_000` | Max chunk size |
| `log` | `True` | Enable logging |

**Returns:** `List` - update results per chunk.

> **Note:** Update API does NOT support `allowAdditionalAttributes`. Fields not in layer schema are silently filtered out.

---

## Query

### query_layer_to_gdf
Query layer features and return as GeoDataFrame.

```python
from evergis_tools.features import query_layer_to_gdf

gdf = query_layer_to_gdf(
    client, "john_doe.my_layer",
    conditions=["WHERE status = @status"],
    parameters={"@status": "active"},
    attributes=["name", "price", "geometry"],
    limit=1000,
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `layer_name` | `None` | Layer system name |
| `layer_path` | `None` | Catalog path (alternative) |
| `attributes` | `None` | List of fields to fetch (None = all) |
| `conditions` | `None` | List of WHERE conditions |
| `limit` | `None` | Max features to return |
| `offset` | `None` | Pagination offset |
| `parameters` | `None` | `@param` substitution dict |
| `sort` | `None` | List of sort fields |
| `sr_id` | `4326` | Geometry coordinate system |
| `with_geom` | `True` | Include geometry |
| `target_crs` | `"EPSG:4326"` | Target CRS for GeoDataFrame |
| `log` | `True` | Enable logging |

**Returns:** `gpd.GeoDataFrame`

> **Note:** `conditions` is a **list** of strings, not a single string.

> **Note:** each condition is a full `WHERE ...` clause - include the
> leading `WHERE`. The same holds for `delete_features_by_condition`. A
> condition with a string literal but no `WHERE` (e.g. `status = 'x'`) is
> rejected by the server with a PostgreSQL error. `count_features` is
> lenient and adds the `WHERE` for you, but writing it explicitly keeps
> all the filter calls consistent.

---

## Convert

### df_to_features
Convert pandas DataFrame (no geometry) to list of FeatureDc.

```python
from evergis_tools.features import df_to_features

features = df_to_features(df)
```

**Params:** `df` (DataFrame), `log=True`

**Returns:** `List[FeatureDc]` - IDs are auto-generated by server, no ID column needed.

### gdf_to_update_features
Convert GeoDataFrame to list of UpdateFeatureDc for batch editing.

```python
from evergis_tools.features import gdf_to_update_features

update_features = gdf_to_update_features(gdf, target_sr=4326, id_column="gid")
```

**Params:** `gdf`, `target_sr=3857`, `geometry_type=None`, `id_column="id"`, `log=True`

**Returns:** `List[UpdateFeatureDc]`

> **Warning:** Raises `ValueError` if `id_column` not found in GDF or contains empty values. ID column is auto-cast to string.

### df_to_update_features
Convert DataFrame to list of UpdateFeatureDc (no geometry).

```python
from evergis_tools.features import df_to_update_features

update_features = df_to_update_features(df, id_column="gid")
```

**Params:** `df`, `id_column="id"`, `log=True`

**Returns:** `List[UpdateFeatureDc]`

> **Warning:** Raises `ValueError` if `id_column` not found or contains empty values. ID column is auto-cast to string.

### gdf_to_paged_feature_list
Convert GeoDataFrame to PagedFeaturesListDc (Pydantic model with pagination metadata).

```python
from evergis_tools.features import gdf_to_paged_feature_list

paged = gdf_to_paged_feature_list(gdf, offset=0, limit=100, target_sr=4326)
print(f"Total: {paged.totalCount}, Page: {len(paged.features)}")
```

**Params:** `gdf`, `offset=0`, `limit=None` (all), `target_sr=4326`, `geometry_type=None`

**Returns:** `PagedFeaturesListDc`

### chunk_features_by_size
Split features list by JSON payload size (not count). See [[Patterns - Chunking]].

```python
from evergis_tools.features import chunk_features_by_size

chunks = chunk_features_by_size(features, max_chunk_size_bytes=5_000_000)
```

**Params:** `features: List`, `max_chunk_size_bytes=5_000_000`, `log=False`

**Returns:** `List[List]` - list of chunks.

---

## See Also
- [[Layers/Layers|Layers]] - Create layers before adding features
- [[EQL]] - Query data via EQL (alternative to `query_layer_to_gdf`)
- [[GeoDataFrames]] - Lower-level conversion functions
- [[Patterns - Chunking]] - How chunking works
