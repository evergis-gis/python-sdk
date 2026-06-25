---
title: Export (Tasks)
module: evergis_tools.tasks.export_tools
---

# Export (Tasks)

Run a server-side `importExport` task that writes a layer (or a filtered EQL slice of one) out to a CSV / XLSX / Shapefile / GPKG / GeoJSON `File` resource in the catalog. Import: `from evergis_tools.tasks.export_tools import ...`

## Workflow

A typical export is three calls: pick the source layer, build identity mappings from its schema, run the matching exporter, then locate the resulting `File` resource in the target folder.

```python
from evergis_tools import Client, create_export_mappings_from_layer
from evergis_tools.catalog import delete_resource
from evergis_tools.tasks.export_tools import export_layer_to_gpkg

with Client() as client:
    username = client.account.get_user_info().username
    source = f"{username}.evg_overture_metro_stations"
    parent = f"{username}/EverGIS Resources/python/tasks/results"
    target_file = "evg_export_metro.gpkg"

    delete_resource(client, f"{parent}/{target_file}", missing_ok=True)

    attr_map, type_map = create_export_mappings_from_layer(client, source)

    result = export_layer_to_gpkg(
        client=client,
        source_layer=source,
        target_file_name=target_file,
        target_parent_path=parent,
        attribute_mapping=attr_map,
        attribute_type_mapping=type_map,
    )
    print(result.status, result.duration)
```

## Export Functions

One function per target format. All return `TaskExecutionResult` (or a `TaskStep` when `defer=True`).

| Format | Function | Geometry handling |
|--------|----------|-------------------|
| CSV | `export_layer_to_csv` | Via `coord_source_fields` / WKT column |
| XLSX | `export_layer_to_xlsx` | Via `coord_source_fields` / WKT column |
| Shapefile | `export_layer_to_shapefile` | Native |
| GeoPackage | `export_layer_to_gpkg` | Native |
| GeoJSON | `export_layer_to_geojson` | Native |

### Common parameters

Shared by every `export_layer_to_*`:

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | Authenticated `evergis_api.Client` |
| `source_layer` | required | Source layer system name (e.g. `john_doe.evg_<short>`). Empty string raises `ValueError` |
| `source_eql` | `None` | Full EQL query. When set, the helper builds `SourceEqlConfig(eql=source_eql)` and `source_layer_condition` is dropped |
| `source_layer_condition` | `None` | Additional `WHERE` baked into `SourceEqlConfig(layer_name=source_layer, condition=...)` when `source_eql` is not provided |
| `target_file_name` | required | Output file name (e.g. `cities.gpkg`) when `target_parent_path` is set, otherwise a full catalog path / resource ID. Empty string raises `ValueError` |
| `target_parent_path` | `None` | Catalog folder for the output file. Resolved through `resolve_resource`, which creates missing path segments via `get_or_create_folder_by_path` (see [[Catalog/Folders\|Folders]]) |
| `attribute_mapping` | `None` | `{source_field: target_field}` rename map. Build with [[Layers/Read\|create_export_mappings_from_layer]] |
| `attribute_type_mapping` | `None` | `{field: EverGISType}` - `Int32`, `Double`, `String`, `Point`, ... |
| `default_values` | `None` | `{field: value}` defaults forwarded as-is to the worker |
| `batch_count` | `50000` | Streaming batch size |
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

**Shapefile / GeoPackage / GeoJSON** declare a single optional field:

| Param | Default | Description |
|-------|---------|-------------|
| `target_layer_name` | `None` | Layer name inside the container. Forwarded to the worker as `target_layerName` |

> **Warning:** `export_layer_to_gpkg` accepts `target_layer_name` but the line that forwards it (`target_layerName=target_layer_name`) is **commented out** in `export_layer_to_gpkg.py`. Passing this argument has no effect on GPKG output. The Shapefile and GeoJSON exporters forward it correctly.

**CSV** (`export_layer_to_csv`) and **XLSX** (`export_layer_to_xlsx`) share the tabular-format options - geometry is emitted via explicit coordinate columns, not natively:

| Param | Default | Description |
|-------|---------|-------------|
| `coord_source_fields` | `None` | Iterable of X/Y output column names for geometry layers. Coerced to `list` if provided |
| `spatial_reference` | `4326` | SRID for the emitted coordinates |
| `is_wkt` | `False` | Write geometry as a single WKT column instead of X/Y |
| `attribute_name_row_number` | `None` | Row number carrying field names |
| `alias_row_number` | `None` | Row number carrying field aliases |
| `first_data_row_number` | `None` | Row where data starts |

CSV additionally takes `column_delimiter` (default `";"`). XLSX has no extra parameters.

## Key Behaviors

- **Source filter is `SourceEqlConfig` either way.** When `source_eql` is truthy the helper builds `SourceEqlConfig(eql=source_eql)` and `source_layer_condition` is ignored. Otherwise it builds `SourceEqlConfig(layer_name=source_layer, condition=source_layer_condition)`. Both branches feed the same server-side path.
- **Auto-folder creation.** When `target_parent_path` is set, `resolve_resource` is called against it (creating missing folder segments) and `target_file_name` is forwarded to the worker as-is. Without `target_parent_path`, `target_file_name` is resolved through `resolve_resource` and the resolved `resourceId` is passed instead. See [[Catalog/Folders\|Folders]].
- **No client-side mappings check.** None of the exporters raise when `attribute_mapping` or `attribute_type_mapping` is `None`. Building them with [[Layers/Read\|create_export_mappings_from_layer]] is the recommended path - it reads the layer schema and returns the identity rename plus `{field: EverGISType}` ready to pass through.
- **Locating the produced file.** The exporter creates a new `File` resource in `target_parent_path`. The `TaskExecutionResult` does not carry the new file's resource ID. List the parent folder via `client.catalog.post_get_all(ListResourcesDc(parentId=...))` and match on the file name.

> **Note:** Re-running an export against the same `target_file_name` does not overwrite the previous file. Drop the existing `File` resource first (`delete_resource(client, path, missing_ok=True)` from `evergis_tools.catalog`) to keep the folder tidy across reruns.

## See Also
- [[Tasks]] - task execution, result models, progress callbacks
- [[Tasks/Import|Import]] - the reverse direction (file -> layer)
- [[Catalog/Files|Files]] - downloading the produced file resource locally
- [[Layers/Read|Read Layer]] - `create_export_mappings_from_layer` and other layer-schema helpers
