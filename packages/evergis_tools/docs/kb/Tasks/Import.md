---
title: Import (Tasks)
module: evergis_tools.tasks.import_tools
---

# Import (Tasks)

Run a server-side `importExport` task that loads a CSV / XLSX / Shapefile / GPKG / FGDB file - already uploaded to the catalog as a `File` resource - into an EverGIS layer. Import: `from evergis_tools.tasks.import_tools import ...`

## Workflow

The full path from a local file to a populated layer is four steps:

1. Upload the file to the catalog (see [[Catalog/Files|Files]]).
2. Ask the server for its schema via `get_<format>_data_schema_rest`.
3. Derive `attribute_mapping` / `attribute_type_mapping` via `build_attribute_mappings_from_schema`.
4. Run the matching `import_<format>_to_layer`.

```python
from evergis_tools import Client
from evergis_tools.catalog.resources import resolve_resource
from evergis_tools.tasks.import_tools import (
    get_gpkg_data_schema_rest,
    build_attribute_mappings_from_schema,
    import_gpkg_to_layer,
)

with Client() as client:
    source = "john_doe/EverGIS Resources/python/import/source_files/ne_110m.gpkg"
    target = "john_doe.evg_gpkg_countries"
    parent = "john_doe/EverGIS Resources/python/import/results"

    # Cleanup before import - see Key Behaviors.
    try:
        existing = resolve_resource(client, target)
        client.catalog.delete_resource(resourceId=existing.resourceId, cascade=True)
    except ValueError:
        pass

    schema = get_gpkg_data_schema_rest(client, source, layer_name="countries")
    attr_map, type_map = build_attribute_mappings_from_schema(schema)

    result = import_gpkg_to_layer(
        client=client,
        source_file_name=source,
        source_layer_name="countries",
        target_layer=target,
        target_layer_parent_path=parent,
        attribute_mapping=attr_map,
        attribute_type_mapping=type_map,
    )
    print(result.status, result.duration)
```

## Import Functions

One function per source format. All return `TaskExecutionResult` (or a `TaskStep` when `defer=True`).

| Format | Function | Schema discovery |
|--------|----------|------------------|
| CSV | `import_csv_to_layer` | `get_csv_data_schema_rest` |
| XLSX | `import_xlsx_to_layer` | `get_xlsx_data_schema_rest` |
| Shapefile (ZIP) | `import_shapefile_to_layer` | `get_shapefile_data_schema_rest` |
| GeoPackage | `import_gpkg_to_layer` | `get_gpkg_data_schema_rest` |
| File Geodatabase | `import_fgdb_to_layer` | `get_fgdb_data_schema_rest` |

### Common parameters

Shared by every `import_*_to_layer`:

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | Authenticated `evergis_api.Client` |
| `source_file_name` | required | Catalog path, resource ID, or system name of the uploaded source file |
| `target_layer` | required | Target layer system name (e.g. `john_doe.evg_<short>`) |
| `target_layer_alias` | `None` | Display name shown in the EverGIS UI |
| `target_layer_parent_path` | `None` | Catalog folder for the new layer. Missing folders are auto-created (see [[Catalog/Folders|Folders]]) |
| `attribute_mapping` | `None` | `{source_field: target_field}`. Build with `build_attribute_mappings_from_schema` |
| `attribute_type_mapping` | `None` | `{field: EverGISType}` - `Int32`, `Double`, `String`, `Point`, ... |
| `enabled` | `True` | Enable the prototype after creation |
| `start_if_previous_error` | `True` | Start even if the previous run errored |
| `start_if_previous_not_finished` | `False` | Start while a previous run is still active |
| `order`, `description` | `None` | Subtask order and prototype description |
| `wait_for_completion` | `True` | Block until the run finishes |
| `timeout` | `300` | Wait timeout in seconds; `None` disables |
| `check_interval` | `2.0` | Status polling interval in seconds |
| `progress_callback` | `None` | Callback `(TaskProgress) -> None` (see [[Tasks]]) |
| `log` | `False` | Print prototype JSON and execution statuses |
| `defer` | `False` | Return a `TaskStep` instead of running - drop into a `TaskPipeline` to batch several subtasks under one prototype |

### Format-specific parameters

**CSV** (`import_csv_to_layer`):

| Param | Default | Description |
|-------|---------|-------------|
| `source_coord_fields` | `None` | Names of X/Y columns; geometry is then added to `attribute_mapping` automatically |
| `column_delimiter` | `";"` | Column separator |
| `spatial_reference` | `4326` | SRID of source coordinates |
| `is_wkt` | `False` | Source has a single WKT geometry column |
| `contains_alias_row` | `False` | CSV has a row with field aliases |
| `attribute_name_row_number`, `alias_row_number`, `first_data_row_number` | `None` | 1-based row numbers; server picks sensible defaults when omitted |
| `default_values` | `None` | `{field: value}` for fields missing in the source |

**XLSX** (`import_xlsx_to_layer`):

Same as CSV minus `column_delimiter`, `contains_alias_row`, `default_values`. The server reads the first sheet; multi-sheet selection is not exposed here.

**Shapefile** (`import_shapefile_to_layer`):

| Param | Default | Description |
|-------|---------|-------------|
| `source_layer_name` | required | Layer name inside the ZIP (single-layer archives still require it) |
| `default_values` | `None` | Same as CSV |

No `spatial_reference` / `is_wkt` - SRID is read from the bundled `.prj`.

**GeoPackage** (`import_gpkg_to_layer`) and **File Geodatabase** (`import_fgdb_to_layer`):

| Param | Default | Description |
|-------|---------|-------------|
| `source_layer_name` | required | Layer (GPKG) or feature class (FGDB) inside the container |
| `default_values` | `None` | Same as CSV |

Both formats are containers - one call imports one layer. Loop over the schema's `layers[]` to load every layer of a multi-layer file. FGDB archives are uploaded as `.gdb.zip`.

## Schema Discovery

`get_<format>_data_schema_rest` calls the worker REST method `importExport/dataSchema` and returns the raw server response (`{layers: [{name, attributesConfiguration: {attributes: [...]}}, ...]}`). For container formats (GPKG, FGDB) pass `layer_name=` to fetch a single layer; omit it to list every layer in the file. Shapefile and CSV/XLSX have a single implicit layer.

`build_attribute_mappings_from_schema(schema, layer_name=None, include_geometry=True)` turns that response into the two dicts the importer expects - an identity mapping plus the server-reported types. This replaces the per-example boilerplate of hand-writing every column name.

```python
from evergis_tools.tasks.import_tools import (
    get_csv_data_schema_rest,
    build_attribute_mappings_from_schema,
)

schema = get_csv_data_schema_rest(
    client,
    "john_doe/.../charging_stations.csv",
    column_delimiter=",",
    attribute_name_row_number=1,
    first_data_row_number=2,
)
attr_map, type_map = build_attribute_mappings_from_schema(schema)
# attr_map: {"name": "name", "kw": "kw", "geometry": "geometry", ...}
# type_map: {"name": "String", "kw": "Int32", "geometry": "Point", ...}
```

Pass `include_geometry=False` to skip the geometry attribute (useful when importing a CSV table without coordinates).

## Key Behaviors

- **Recommended cleanup before import (convention, not enforced by these functions).** The server refuses to recreate a layer over an existing physical table - the second run fails with `table already exist`. The convention is to delete the target layer first via `client.catalog.delete_resource(resourceId=..., cascade=True)` (cascade is mandatory, otherwise the orphan DB table survives the delete). Exception: append/upsert flows that explicitly target an existing layer.
- **Auto-folder creation.** `target_layer_parent_path` is resolved through `get_or_create_folder_by_path`; missing path segments are created on the fly. See [[Catalog/Folders|Folders]].
- **Source file lives in the catalog.** `source_file_name` is resolved against the catalog (path / resource ID / system name) - upload via [[Catalog/Files|Files]] first. There is no local-disk path support here.
- **Geometry from coordinate columns (CSV/XLSX).** Passing `source_coord_fields=("lon", "lat")` injects `{"geometry": "geometry"}` into `attribute_mapping` automatically - you do not need to add it by hand.
- **Container formats are per-layer.** GPKG and FGDB calls import exactly one `source_layer_name`. Iterate over `schema["layers"]` in the caller to load every layer.
- **Returns.** `TaskExecutionResult` (`status`, `is_successful`, `duration`, `error_message`, `subtasks`, ...) - see [[Tasks]] for the full model. When `defer=True`, returns a `TaskStep` for batching inside a `TaskPipeline`.

## See Also
- [[Tasks]] - task execution, result models, progress callbacks
- [[Tasks/Export|Export]] - the reverse direction (layer -> file)
- [[Catalog/Files|Files]] - upload a local file to the catalog before importing
- [[Layers/Create|Create Layer]] - create an empty layer from a schema (no source file)
- [[Attributes]] - EverGIS attribute types referenced in `attribute_type_mapping`
