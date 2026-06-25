---
title: Geoprocessing (Tasks)
module: evergis_tools.tasks.geoprocessing
---

# Geoprocessing (Tasks)

Run server-side `geoProcessing` tasks that copy / update / delete / union features through an EQL source, or validate and fix layer geometries. Import: `from evergis_tools.tasks.geoprocessing import ...`

## EQL Operations

Four wrappers around the `geoProcessing` worker that take an EQL query as the feature source. All return `TaskExecutionResult` (or a `TaskStep` when `defer=True`).

| Function | What it does | Target |
|----------|--------------|--------|
| `copy_layer_via_eql` | Copy features matched by EQL into a **new** layer | Created |
| `update_layer_via_eql` | Update an existing layer from features returned by EQL, matched by `source_id_attribute` | In-place |
| `delete_from_layer_via_eql` | Delete features whose ids are returned by the EQL source | In-place |
| `union_layers_via_eql` | Geometric union (dissolve) of features into a single feature, or one per group value | Created |

### Workflow

```python
from evergis_tools import Client
from evergis_tools.catalog import delete_resource
from evergis_tools.tasks.geoprocessing import copy_layer_via_eql

with Client() as client:
    username = client.account.get_user_info().username
    source = f"{username}.evg_overture_places"
    target = f"{username}.evg_gp_cafes"
    parent = f"{username}/EverGIS Resources/python/geo_tools/results"

    delete_resource(client, target, missing_ok=True)

    result = copy_layer_via_eql(
        client=client,
        eql=f"SELECT * FROM {source} WHERE category = @cat",  # see EQL placeholders
        target_layer=target,
        target_layer_parent_path=parent,
    )
    print(result.status, result.duration)
```

### Common parameters

Shared by every EQL operation:

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | Authenticated `evergis_api.Client` |
| `eql` | required | EQL query that defines the source dataset |
| `target_layer` | required | Target layer system name (e.g. `john_doe.evg_<short>`) |
| `target_layer_alias` | `None` | Display name shown in the EverGIS UI |
| `source_condition` | `None` | Extra `WHERE` appended to the EQL on the server side |
| `source_id_attribute` | `"gid"` | Identifier attribute returned by the source query |
| `source_geometry_attribute` | `"geometry"` | Geometry attribute returned by the source query |
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

### Per-function differences

**`copy_layer_via_eql`** adds `target_layer_parent_path` (auto-created via `resolve_target_layer_parent`) and `columns_mapping` (`{source_field: target_field}` rename map). Creates the target layer if it does not exist; schema is inferred from the EQL projection.

**`update_layer_via_eql`** takes `target_layer_parent_id` (raw resource id, no path resolution) and `cached: bool = True` - this kwarg is sent on the wire as `materializedView`, asking the worker to pre-materialise the EQL source. The worker matches rows by `source_id_attribute` (default `gid`); missing-id behaviour is server-side and not asserted here.

**`delete_from_layer_via_eql`** has the same shape as update (no `cached`). The EQL just needs to return the ids of rows to drop; geometry is not used. Submitted under task type `delete` (not `geoProcessing`).

**`union_layers_via_eql`** adds `group_attribute` and `target_layer_parent_path`. Without `group_attribute` the whole source collapses into one feature; with it, one feature per distinct group value. Submitted under task type `geoProcessing:union`.

## Geometry Validation

Two wrappers around the `geoProcessing:validateGeometry` / `geoProcessing:fixGeometry` workers.

### validate_layer_geometry
Validate geometries in a layer (or in an EQL slice of one) and write the **invalid** ones to a new layer along with the error reason.

```python
from evergis_tools.tasks.geoprocessing import validate_layer_geometry

result = validate_layer_geometry(
    client,
    source_layer="john_doe.evg_buildings",          # layer name OR full EQL
    target_layer="john_doe.evg_buildings_invalid",
    invalid_reason_column="validation_error",
)
```

**Key params:** `client`, `source_layer` (treated as EQL when it contains `SELECT`/`FROM`, as a layer name otherwise), `target_layer`, `target_layer_alias`, `target_layer_parent_id`, `invalid_reason_column` (default `validation_error`), `base_object_id_attribute` (default `source_object_id` - column holding the source feature id), `source_condition`, `source_id_attribute`, `source_geometry_attribute`, `materialized_view` (cache EQL source - default `False`). Plus the standard `enabled` / `start_if_*` / `wait_for_completion` / `timeout` (300s) / `check_interval` / `progress_callback` / `log` / `defer`.

**Returns:** `TaskExecutionResult`. The invalid features land in `target_layer` - inspect that layer for the per-feature reason.

### fix_layer_geometry
Repair invalid geometries **in place** in `layer_name` via the server-side fix worker (`geoProcessing:fixGeometry`). No source EQL - the worker walks the whole layer. The docstring mentions `buffer(0)` / `make_valid` as example algorithms; the actual algorithm is server-side.

```python
from evergis_tools.tasks.geoprocessing import fix_layer_geometry

result = fix_layer_geometry(client, layer_name="john_doe.evg_buildings", timeout=900)
```

**Key params:** `client`, `layer_name`. Plus the standard `enabled` / `start_if_*` / `wait_for_completion` / `timeout` (default `600` - 10 min) / `check_interval` / `progress_callback` / `log` / `defer`.

**Returns:** `TaskExecutionResult`. The original layer is mutated; no copy is produced.

## Key Behaviors

- **Parameterise the EQL.** The `eql=` and `source_condition=` strings are sent to the server verbatim - never `f`-string user input into them. Use the `@name` / `${isset:}` placeholders the EQL engine accepts. See [[EQL]] for the syntax and the [[Patterns - StringFormat|string-format patterns]] for safe building.
- **`copy_layer_via_eql` creates, `update_layer_via_eql` mutates.** Copy creates the target layer; the server rejects creation when the underlying table already exists (`table already exist`) - drop the resource first with `delete_resource(..., missing_ok=True)`. Update matches by `source_id_attribute` (default `gid`).
- **`delete_from_layer_via_eql` is id-driven.** Only the column named in `source_id_attribute` matters in the EQL output; geometry and other columns are ignored.
- **`union_layers_via_eql` dissolves features.** Submitted under task type `geoProcessing:union` - a geometric union over the EQL source, not a SQL `UNION ALL` of two layers. Pass `group_attribute="region"` to get one feature per group value; omit it to dissolve the whole input. Pre-filter via the EQL itself - the worker has no separate input-layers list.
- **`validate_layer_geometry` writes a results layer, not a list.** Invalid features are persisted to `target_layer` with the error text in `invalid_reason_column` and the original id in `base_object_id_attribute`. Pair with [[Layers/Read|Read Layer]] to iterate the failures, or pipe straight into `fix_layer_geometry` against the source.
- **`fix_layer_geometry` is in-place and only takes a layer name.** No EQL filter, no copy - the original layer is mutated. Default timeout is 600s (10 minutes); raise it for large layers.
- **`materialized_view` / `cached` are the same wire option.** Both kwargs serialise to `materializedView` in the start parameters and ask the worker to pre-materialise the EQL source. `update_layer_via_eql` exposes it as `cached` (default `True`); `validate_layer_geometry` exposes it as `materialized_view` (default `False`).
- **Returns.** `TaskExecutionResult` (`status`, `is_successful`, `duration`, `error_message`, `subtasks`, ...) - see [[Tasks]] for the full model. When `defer=True`, returns a `TaskStep` for batching inside a `TaskPipeline`.

## See Also
- [[Tasks]] - task execution, result models, progress callbacks
- [[Tasks/Import|Import]] - load features from a file into a layer
- [[Tasks/Export|Export]] - write a layer (or EQL slice) out to a file
- [[EQL]] - EQL syntax and parameter placeholders for `eql=` / `source_condition=`
- [[Layers/Update|Layers Update]] - direct attribute / feature edits without a geoProcessing task
