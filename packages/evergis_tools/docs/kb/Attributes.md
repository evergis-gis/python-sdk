---
title: Attributes
module: evergis_tools.attributes
---

# Attributes

Type conversion and field validation utilities. Import: `from evergis_tools.attributes import ...`

Public functions in source:

- `pydantic_to_attribute_type` - re-exported from `evergis_tools` root.
- `validate_gdf_fields_by_layer` - re-exported from `evergis_tools` root.
- `clean_attributes_for_evergis` - public in `attributes.py`, not re-exported from root. Used internally by `geodataframes` and `features` add/edit pipelines.

The module has no `__all__`; all `_`-prefixed helpers (`_pandas_dtype_to_attribute_type`, `_get_geometry_attribute_type`, `_detect_field_type`, `_clean_*`, `_is_*`, `_types_compatible`, `_convert_numpy_to_python`) are private.

## pydantic_to_attribute_type
Convert a Python / Pydantic type annotation to `AttributeType`.

```python
from datetime import datetime
from typing import Optional
from evergis_tools.attributes import pydantic_to_attribute_type

pydantic_to_attribute_type(int)                # AttributeType.INT64
pydantic_to_attribute_type(str)                # AttributeType.STRING
pydantic_to_attribute_type(float)              # AttributeType.DOUBLE
pydantic_to_attribute_type(bool)               # AttributeType.BOOLEAN
pydantic_to_attribute_type(datetime)           # AttributeType.DATETIME
pydantic_to_attribute_type(list)               # AttributeType.JSON
pydantic_to_attribute_type(dict)               # AttributeType.JSON
pydantic_to_attribute_type(Optional[str])      # AttributeType.STRING (unwraps Union)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `python_type` | required | Python type annotation |
| `field_name` | `""` | Field name, used only for debug logging |

**Returns:** `AttributeType`

Mapping (from `type_map` in source):

- `int` -> `INT64`
- `str` -> `STRING`
- `float` -> `DOUBLE`
- `bool` -> `BOOLEAN`
- `datetime`, `date` -> `DATETIME` (no separate DATE type)
- `list`, `dict` -> `JSON`
- `type(None)` -> `STRING`

`Union` / `Optional` types are unwrapped to the first non-`None` arg and recursed.
Generic `list[...]` / `dict[...]` annotations (with `__origin__`) map to `JSON`.
Unknown types fall back to `STRING` with a debug log entry.

## validate_gdf_fields_by_layer
Validate that a GeoDataFrame matches a layer schema.

```python
from evergis_tools import get_layer_schema
from evergis_tools.attributes import validate_gdf_fields_by_layer

schema = get_layer_schema(client, "john_doe.my_layer")
is_valid, errors = validate_gdf_fields_by_layer(
    gdf=my_gdf,
    layer_schema=schema,
    check_types=True,
)
if not is_valid:
    for err in errors:
        print(err)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `gdf` | required | GeoDataFrame to validate |
| `layer_schema` | required | `AttributesConfigurationDc` from `get_layer_schema()` |
| `check_types` | `False` | Also validate field types against schema |
| `strict` | `False` | Raise `ValueError` on failure instead of logging |
| `log` | `True` | Emit warning / info via module logger |

**Returns:** `tuple[bool, list[str]]` - `(is_valid, error_messages)`.

**Raises:** `ValueError` when `strict=True` and validation fails.

Checks performed:

1. Extra columns not in schema produce a warning entry (they will be excluded by downstream code).
2. With `check_types=True`, GDF dtype is converted via the private `_pandas_dtype_to_attribute_type` and compared via the private `_types_compatible`. The compatibility rules are:
   - exact match,
   - any pair within `{INT32, INT64, DOUBLE}`,
   - any pair within `{STRING, JSON}`,
   - any pair within the geometry set `{POINT, LINESTRING, POLYGON, MULTIPOINT, MULTILINESTRING, MULTIPOLYGON}`.

> **Note:** If `layer_schema.attributes` is falsy the function returns `(True, [])` after a single warning, without checking the GDF.

## clean_attributes_for_evergis
Normalise a feature attributes dict before sending it to the server.

```python
from evergis_tools.attributes import clean_attributes_for_evergis

clean_attributes_for_evergis({
    "count": None,
    "active": True,
    "tags": ["a", "b"],
})
# {'count': None, 'active': True, 'tags': ['a', 'b']}
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `attributes` | required | Original `Dict[str, Any]` of feature properties |

**Returns:** `Dict[str, Any]` - cleaned attributes ready for `FeatureDc.properties`.

Per-value rules (from `_clean_single_attribute` dispatch):

- `None`, pandas NaN, and string forms in `NULL_STRING_VALUES` -> `None`.
- `bool` -> passed through (checked before `int` because `bool` is a subclass of `int`).
- `int` / `float` -> passed through, NaN becomes `None` when pandas is importable.
- `str` -> passed through unless it matches a null-string sentinel.
- `list` / `dict` / `tuple` -> recursively unwrapped from numpy types to native Python; tuples become lists; empty collections become `None`.
- Anything else -> `str(value)`, unless empty / null-like, in which case `None`. Raises `ValueError` if `str(...)` itself fails.

> **Warning:** Collections are returned as native Python `list` / `dict`, not stringified JSON. The server silently drops `json.dumps(...)` output for `Json` columns; the value must reach `properties.<column>` as a native JSON array or object.

## Specialized Attribute Types

For server-side `StringSubType` columns (attachments, calculated expressions) use the typed builders in [[AttributeTypes/AttributeTypes|AttributeTypes]]:

- [[AttributeTypes/Attachments|Attachments]] - file attachments column
- [[AttributeTypes/Calculated|Calculated]] - server-side computed column via EQL expression

## See Also
- [[AttributeTypes/AttributeTypes|Attribute Types]] - typed helpers for specialised subType columns
- [[Layers/Layers|Layers]] - layer creation uses attribute types
- [[GeoDataFrames]] - uses `clean_attributes_for_evergis` internally
