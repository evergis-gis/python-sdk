---
title: Layers - Create
module: evergis_tools.layers.create
---

# Layer Creation

Import: `from evergis_tools.layers import gdf_to_layer, create_layer_from_schema, create_query_layer`

## Common Behaviors

All create functions share these behaviors:

- **Name normalization** - Cyrillic transliterated to Latin, lowercased, snake_case. `"Мои Участки"` → `"username.moi_uchastki"`. Username prefix added automatically.
- **Auto-folder creation** - `parent_path="john_doe/Projects/Data/2024"` creates missing folders automatically.
- **gid attribute** - mandatory `gid` added if not present in schema; PK constraints and autoincrement are applied server-side.
- **Overwrite modes** - see [[Patterns - Overwrite]]
- **Name/alias collision** - if a resource with the same system name or alias already exists in the target folder, publishing raises `ResourceExists` (HTTP 409). The v3 catalog enforces unique `owner/folder/alias` paths, so this fires on an alias clash even when `overwrite=True` freed the system name. See [[Errors]].

---

## gdf_to_layer

Create layer from GeoDataFrame with automatic attribute schema inference from dtypes.

```python
from evergis_tools.layers import gdf_to_layer

result = gdf_to_layer(
    client, gdf, "my_layer",
    layer_alias="My Layer",
    geometry_type="Point",
    srid=4326,
    overwrite=True,
    parent_path="john_doe/Projects/Folder",
    order_attribute="sort_col",
)
```

**All params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `gdf` | required | GeoDataFrame with data |
| `layer_name` | required | Layer name (auto-normalized) |
| `layer_alias` | `None` | Human-readable name |
| `srid` | `4326` | Spatial reference |
| `id_attribute` | `"gid"` | ID field name |
| `geometry_attribute` | `"geometry"` | Geometry field name |
| `create_table` | `True` | Create physical PostgreSQL table |
| `overwrite` | `False` | `False` / `True` / `"cascade"` |
| `geometry_type` | `None` | `"Point"`, `"Polygon"`, `"MultiPolygon"`, etc. |
| `parent_path` | `None` | Catalog path (auto-creates missing folders) |
| `client_style` | `None` | Mapbox GL style dict |
| `order_attribute` | `None` | Attribute for feature ordering |
| `log` | `True` | Enable logging |

**Returns:** `list` - deletion responses (if overwrite) + publish response.

**Notes:**
- Attribute types inferred from pandas dtypes (int64→INT64, object→STRING, float64→DOUBLE, etc.)
- If geometry column missing in GDF, layer created without geometry
- `order_attribute` sets the attribute used for feature ordering in the layer

---

## create_layer_from_schema

Create layer from Pydantic model schema. Useful when you know the schema upfront and want precise type control.

```python
from pydantic import BaseModel, Field
from evergis_tools.layers import create_layer_from_schema

class CitySchema(BaseModel):
    name: str = Field(..., description="City name")
    population: int = Field(..., description="Population")
    area: float = Field(0.0, description="Area in km2")

result = create_layer_from_schema(
    client, schema=CitySchema, layer_name="cities",
    geometry_field="geometry", geometry_type="Point",
    srid=4326, overwrite=True,
)
```

**All params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `schema` | required | Pydantic BaseModel class |
| `layer_name` | required | Layer name (auto-normalized) |
| `layer_alias` | `None` | Human-readable name |
| `srid` | `4326` | Spatial reference |
| `id_attribute` | `"gid"` | ID field name |
| `geometry_field` | `None` | Geometry field name in schema |
| `geometry_type` | `None` | Geometry type string |
| `overwrite` | `False` | `False` / `True` / `"cascade"` |
| `parent_path` | `None` | Catalog path |
| `client_style` | `None` | Mapbox GL style dict |
| `card_configuration` | `None` | Popup card dict |
| `edit_configuration` | `None` | Edit form dict |
| `create_table` | `True` | Create physical table |
| `query` | `None` | EQL query (**mandatory** when `create_table=False`) |
| `order_attribute` | `None` | Feature ordering attribute |
| `log` | `True` | Enable logging |

**Returns:** `list` - deletion responses + publish response.

**Geometry field detection priority:**
1. Explicit: `geometry_field="my_geom"` + `geometry_type="Point"`
2. Field metadata: `Field(json_schema_extra={"geometry_type": "Point"})`
3. Auto-detect: field named `"geometry"` defaults to Point

**Type mapping:**
- `int` → INT64, `str` → STRING, `float` → DOUBLE, `bool` → BOOLEAN
- `datetime` → DATETIME, `list`/`dict` → JSON
- `Optional[T]` → uses inner type `T`
- `Field(description="...")` → becomes attribute alias

> **Warning:** When `create_table=False`, the `query` parameter is **mandatory** - raises `ValueError` if missing.

---

## create_query_layer

Create virtual layer from EQL query. No physical table by default - data comes from the query.

```python
from evergis_tools.layers import create_query_layer

result = create_query_layer(
    client, "active_cities",
    eql_query="SELECT * FROM john_doe.cities WHERE status = @status",
    geometry_type="Point",
    eql_parameters={"@status": "active"},
    parent_path="john_doe/Projects/Views",
)
```

**All params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `layer_name` | required | Layer name (auto-normalized) |
| `eql_query` | required | EQL query string |
| `layer_alias` | `None` | Human-readable name |
| `parent_path` | `None` | Catalog path |
| `geometry_type` | `None` | Geometry type |
| `srid` | `4326` | Spatial reference |
| `id_attribute` | `"gid"` | ID field |
| `geometry_attribute` | `"geometry"` | Geometry field |
| `create_table` | `False` | Create physical table (False for views) |
| `overwrite` | `False` | Overwrite mode |
| `description` | `None` | Layer description |
| `condition` | `None` | Additional WHERE filter |
| `eql_parameters` | `None` | Dict of `@param` → value |
| `client_style` | `None` | Mapbox GL style |
| `card_configuration` | `None` | Popup card |
| `edit_configuration` | `None` | Edit form |
| `order_attribute` | `None` | Feature ordering |
| `log` | `True` | Enable logging |

> **Note:** All params after `eql_query` are **keyword-only**.

**Returns:** Single response object (not a list, unlike other create functions).

**EQL parameter auto-conversion:**
```python
# Simple values auto-detected:
eql_parameters={"@status": "active"}   # → String
eql_parameters={"@count": 10}          # → Int64
eql_parameters={"@ratio": 3.14}        # → Double
eql_parameters={"@active": True}       # → Boolean
eql_parameters={"@ids": [1, 2, 3]}     # → Array of Int64
```

---

## See Also
- [[Layers/Read]] - Read layer configuration
- [[Layers/Update]] - Modify existing layers
- [[Features]] - Add features after creation
- [[EQL]] - EQL query language and parameters
- [[Patterns - Overwrite]]
- [[Errors]] - `ResourceExists` on name/alias collision
