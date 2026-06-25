---
title: Network (Tasks)
module: evergis_tools.tasks.network
---

# Network (Tasks)

Batch network-analysis tasks - server-side `netEngine` worker that builds isochrone polygons or origin-destination matrices for entire layers at once. Import: `from evergis_tools.tasks.network import ...`

> **Not to be confused with [[GeoTools]].** `evergis_tools.geo_tools.network.build_isochrone` / `build_route` are **single-point synchronous** worker REST calls (one shape returned in-process). The helpers here are **batch task** wrappers that read a whole source layer and write results into a target layer. Use [[GeoTools]] for ad-hoc one-off shapes, this module for bulk pipelines.

## build_isochrones

Build an availability-area (isochrone) layer via `netEngine:availabilityArea`. Every feature in the source layer becomes an isochrone polygon in the target layer.

```python
from evergis_tools import Client
from evergis_tools.tasks.network import build_isochrones

with Client() as client:
    result = build_isochrones(
        client,
        source_layer_name="john_doe.evg_stations",
        provider_name="sproute_isochrone_pedestrian",
        duration_expression="600",   # seconds, provider-specific
        target_layer="john_doe.evg_stations_iso_10min",
        target_layer_alias="stations - 10 min walk",
        target_layer_parent_id="john_doe/EverGIS Resources/python/network/results",
    )
    print(result.status, result.duration)
```

### Parameters

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | Authenticated `evergis_api.Client` |
| `source_layer_eql` | `None` | EQL expression describing the source dataset (alternative to `source_layer_name`) |
| `source_layer_name` | `None` | Existing layer system name to use when EQL is not provided |
| `source_condition` | `None` | Extra filter appended to the source definition |
| `source_id_attribute` | `"gid"` | Identifier attribute in the source |
| `source_geometry_attribute` | `"geometry"` | Geometry attribute in the source |
| `provider_name` | `sproute_isochrone_pedestrian` | NetEngine provider; `ProvidernameType` enum or its string value |
| `duration_expression` | `None` | Reach time / distance expression (provider-specific) |
| `id_attribute_name` | `None` | Output attribute name for feature identifier |
| `geometry_attribute_name` | `None` | Output attribute name for geometry |
| `duration_attribute_name` | `None` | Output attribute name for the duration value |
| `base_object_id_attribute_name` | `None` | Output attribute name for the originating source id |
| `route_center_x_attribute_name` | `None` | Output attribute name for centroid X |
| `route_center_y_attribute_name` | `None` | Output attribute name for centroid Y |
| `target_layer` | `None` | Target layer name to store the resulting polygons |
| `target_layer_alias` | `None` | Display alias of the target layer |
| `target_layer_parent_id` | `None` | Parent source identifier (catalog folder) for the target layer |
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

Either `source_layer_eql` or `source_layer_name` must be provided (otherwise `ValueError`).

## build_od_matrix

Build an origin-destination matrix via `netEngine:ODMatrix`. Every FROM-feature is paired with every TO-feature; one row per pair is written to the target layer.

```python
from evergis_tools import Client
from evergis_tools.tasks.network import build_od_matrix

with Client() as client:
    result = build_od_matrix(
        client,
        target_layer="john_doe.evg_od_stations_to_pois",
        source_from_layer_name="john_doe.evg_stations",
        source_to_layer_name="john_doe.evg_overture_places",
        source_to_condition="category = 'cafe'",
        transport_type="pedestrian",
        target_layer_alias="stations -> cafes (walk)",
        target_layer_parent_id="john_doe/EverGIS Resources/python/network/results",
    )
    print(result.status, result.duration)
```

### Parameters

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | Authenticated `evergis_api.Client` |
| `target_layer` | required | Target layer name to store the resulting matrix |
| `source_from_layer_eql` / `source_from_layer_name` | `None` | EQL or existing layer name for the FROM side (one is required) |
| `source_from_condition` | `None` | Extra filter for the FROM source |
| `source_from_id_attribute` | `"gid"` | FROM identifier attribute |
| `source_from_geometry_attribute` | `"geometry"` | FROM geometry attribute |
| `source_to_layer_eql` / `source_to_layer_name` | `None` | EQL or existing layer name for the TO side (one is required) |
| `source_to_condition` | `None` | Extra filter for the TO source |
| `source_to_id_attribute` | `"gid"` | TO identifier attribute |
| `source_to_geometry_attribute` | `"geometry"` | TO geometry attribute |
| `target_layer_alias` | `None` | Display alias of the target layer |
| `target_layer_parent_id` | `None` | Parent source identifier (catalog folder) for the target layer |
| `transport_type` | `None` | Transport mode for the whole task - `"car"` or `"pedestrian"` |
| `id_attribute_name` | `"gid"` | Output attribute name for the row identifier |
| `id_from_attribute_name` | `"from"` | Output attribute name for the FROM id |
| `id_to_attribute_name` | `"to"` | Output attribute name for the TO id |
| `transport_type_attribute_name` | `"transport_type"` | Output attribute name for the transport type |
| `weight_parameter_attribute_name` | `"weight_parameter"` | Output attribute name for the weight parameter |
| `distance_attribute_name` | `"distance"` | Output attribute name for the distance / metric value |
| `attribute_type_mapping` | `None` | `{attribute_name: type}` for non-`String` types - `Double`, `Int64`, `String`, `Boolean`, `DateTime`. If the target layer already exists, its schema must already contain these attributes |
| `default_values` | `None` | `{attribute_name: value}` written into every row. New attributes are created when the layer does not exist; otherwise they must already be present |
| `enabled` | `True` | Enable the prototype after creation |
| `start_if_previous_error` | `True` | Start even if the previous run errored |
| `start_if_previous_not_finished` | `True` | Start while a previous run is still active |
| `order`, `description` | `None` | Subtask order and prototype description |
| `wait_for_completion` | `True` | Block until the run finishes |
| `timeout` | `300` | Wait timeout in seconds; `None` disables |
| `check_interval` | `2.0` | Status polling interval in seconds |
| `progress_callback` | `None` | Callback `(TaskProgress) -> None` (see [[Tasks]]) |
| `log` | `False` | Print prototype JSON and execution statuses |
| `defer` | `False` | Return a `TaskStep` instead of running - batch under one prototype via `TaskPipeline` |

`target_layer` is mandatory; missing FROM or TO source raises `ValueError`.

## Key Behaviors

- **Worker.** Both helpers create `netEngine:availabilityArea` / `netEngine:ODMatrix` prototypes and dispatch them to the `netEngine` worker. Use [[Tasks]] `manager.get_worker("netEngine")` to verify the worker is alive before running large batches.
- **Server-side `proccessingType` typo.** The wire field is spelled `proccessingType` (double `c`) - this is a known server quirk preserved across the API. The helpers pass it correctly; do not "fix" it when building prototypes by hand.
- **Source addressing.** Pass `source_layer_name` for a plain layer or `source_layer_eql` for a derived dataset (joins, filters, computed columns). `source_condition` adds a WHERE-clause on top of either form. See [[EQL]] for query syntax.
- **Isochrone providers.** `provider_name` accepts `ProvidernameType` enum members or their raw string values; defaults to `sproute_isochrone_pedestrian`. All enum members defined in `worker_models.models.ProvidernameType`: `osrm_car`, `osrm_walk`, `twogis_car`, `twogis_walk`, `sproute_isochrone_car_in`, `sproute_isochrone_car_out`, `sproute_isochrone_pedestrian`. `duration_expression` semantics are provider-specific.
- **Isochrone output schema.** Output attribute names left as `None` are stripped from the payload (`model_dump(exclude_none=True)`); only explicitly set names are sent to the worker. Override any of `id_attribute_name`, `geometry_attribute_name`, `duration_attribute_name`, `base_object_id_attribute_name`, `route_center_x_attribute_name`, `route_center_y_attribute_name` to match an existing target layer schema.
- **OD matrix output schema.** Default columns are `gid` (row id), `from`, `to`, `transport_type`, `weight_parameter`, `distance`. Extend with `attribute_type_mapping` + `default_values` to add typed columns (e.g. tag every row with a `scenario_id` of type `Int64`).
- **Start parameters are typed.** Both helpers serialize via Pydantic models from `evergis_tools.tasks.worker_models` (`NetengineAvailabilityareaStartParameters`, `NetengineOdmatrixStartParameters`, `SourceEqlConfig`, `LayerReferenceConfig`). See [[Tasks/WorkerModels|Worker Models]] for the full type catalogue and how to extend it after regenerating the worker spec.
- **Returns.** `TaskExecutionResult` (`status`, `is_successful`, `duration`, `error_message`, `subtasks`, ...) - see [[Tasks]]. With `defer=True` returns a `TaskStep` for batching inside a `TaskPipeline`.

## See Also
- [[Tasks]] - task execution, result models, progress callbacks, `TaskPipeline`
- [[GeoTools]] - single-point sync version of isochrone / route via worker REST
- [[Tasks/WorkerModels|Worker Models]] - typed start-parameter models used here
- [[EQL]] - source query syntax for `source_layer_eql` / `source_condition`
