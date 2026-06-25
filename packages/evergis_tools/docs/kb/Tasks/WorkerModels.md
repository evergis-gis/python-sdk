---
title: Worker Models
module: evergis_tools.tasks.worker_models
---

# Worker Models

Auto-generated Pydantic models for `StartParameters` of every server-side worker task (netEngine, geoProcessing, importExport, geocodeTask, ...). Import: `from evergis_tools.tasks.worker_models import ...`

**Generated**: do not edit by hand. These models are regenerated from the server's worker task prototypes; the generator derives the common / `ChildrenFields` sets and writes `models.py` plus per-worker `*_conditional.py` modules.

## Base Types

### BaseStartParameters
Empty `BaseModel` that every concrete `*StartParameters` extends. Provides shared Pydantic config (`populate_by_name = True`, so you can pass either the snake_case Python name or the camelCase server alias).

### LayerReferenceConfig
Reference to a target layer the worker should create or write into.

| Field | Alias | Description |
|-------|-------|-------------|
| `name` | - | Layer system name (required) |
| `alias` | - | Display alias |
| `parentId` | - | Parent folder ID |

### SourceEqlConfig
Reference to a source layer, optionally narrowed by an EQL filter. Used as `sourceLayer`, `sourceFromLayer`, `sourceToLayer`, `overlayLayer` in every spatial worker.

| Field | Alias | Description |
|-------|-------|-------------|
| `layer_name` | `layerName` | Source layer system name |
| `eql` | - | EQL expression (see [[EQL]]) |
| `condition` | - | Extra filter merged into the query |
| `id_attribute` | `idAttribute` | ID column override |
| `geometry_attribute` | `geometryAttribute` | Geometry column override |

### Enums
String enums used as field types so values are validated at construction time:

- `ProvidernameType` - routing/isochrone provider (`osrm_car`, `osrm_walk`, `twogis_car`, `twogis_walk`, `sproute_isochrone_car_in`, `sproute_isochrone_car_out`, `sproute_isochrone_pedestrian`).
- `ActionType` - chat-server messaging action (`send_message`, `edit_message`, `create_channel`, `call_offer`, ...).
- `ModelType` - chat worker model (`pro`, `simple`).
- `SourceTypeType` / `TargetTypeType` - importExport source / target formats (`csv`, `gdb`, `kml`, `tab`, `gpkg`, `excel`, `layer`, `shape`, `geojson`, `otherfile`).
- `OperationType` - overlay operation (`Clip`, `Within`, `Intersect`, `Subtraction`, `SymDifference`).

## Helpers

### create_task_prototype
Wrap an already-built `*StartParameters` instance into a `TaskPrototypeDto` ready for `TaskManager.create_and_run`. Re-exported from `evergis_tools.tasks` and used by every high-level wrapper (`import_csv_to_layer`, `export_layer_to_gpkg`, ...).

```python
from evergis_tools.tasks.worker_models import (
    NetengineRouteStartParameters,
    ProvidernameType,
    create_task_prototype,
)

params = NetengineRouteStartParameters(
    providerName=ProvidernameType.OSRM_CAR,
    x1=37.61, y1=55.75, x2=37.65, y2=55.78,
    srIn=4326, srOut=4326,
)
prototype = create_task_prototype(task_type="netEngine", start_parameters=params)
```

`task_type` accepts `mainType` or `mainType:subType`; the implementation does `task_type.split(':', 1)[0]` and forwards only `mainType` to `SubTaskSettingsDto.type` (server requirement).

### create_start_parameters
Factory that picks the right `*StartParameters` class by full task type (`"netEngine:route"`, `"geoProcessing:buffer"`, ...). Useful when the task type is data-driven; prefer the concrete class for static code.

```python
from evergis_tools.tasks.worker_models import create_start_parameters

params = create_start_parameters(
    "geoProcessing:buffer",
    sourceLayer={"layerName": "john_doe.evg_stations"},
    targetLayer={"name": "john_doe.evg_stations_buf"},
    radii=["500"],
)
```

Raises `ValueError` for unknown task types. Does **not** cover `importExport:importExport` - use the conditional `<Source>To<Target>StartParameters` classes directly (see below).

### create_<worker>_<sub>_job
Per-task convenience wrappers (one per concrete `*StartParameters`): `create_netengine_route_job(**params)`, `create_geoprocessing_buffer_job(**params)`, `create_geocodetask_job(**params)`, ... Each builds the params model and calls `create_task_prototype`. Equivalent to the two-step form above; pick whichever reads better at the call site.

## Worker-specific StartParameters

One class per `(mainType, subType)` pair, all subclasses of `BaseStartParameters`. Server field names (camelCase) are exposed via `Field(alias=...)`; pass either form thanks to `populate_by_name = True`.

Representative examples (`models.py` ships 43 `*StartParameters` classes; the same shape applies to the rest):

- `NetengineOdmatrixStartParameters` (`netEngine:ODMatrix`) - `sourceFromLayer` / `sourceToLayer` (`SourceEqlConfig`), `targetLayer` (`LayerReferenceConfig`), `transportType`, `idFromAttributeName`, `idToAttributeName`, `distanceAttributeName`, `attributeTypeMapping`, `defaultValues`.
- `NetengineRouteStartParameters` (`netEngine:route`) - `providerName: ProvidernameType`, `x1`, `y1`, `x2`, `y2`, `srIn`, `srOut`. REST-style worker - no layer references.
- `GeoprocessingBufferStartParameters` (`geoProcessing:buffer`) - `sourceLayer`, `targetLayer`, `radii`, `attributeRadii`, `attributeToCopy`, `materializedView`.
- `GeocodetaskStartParameters` (`geocodeTask:geocodeTask`) - `geocodeProviderName`, `sourceLayer`, `targetLayer`, `geocodeFromGeometry`, `geocodeAddressAttributeName`.
- `ChatserverworkerMessagingprocessStartParameters` (`ChatServerWorker:messaging/process`) - non-spatial worker; `action: ActionType`, `channelId`, `content`, `context`.

The remaining classes (`Chatworker*`, `Universalsearch*`, `EqlhelpworkerEqlhelp*`, `Pythonservice*`, `Geoprocessing{Copy,Update,Delete,Overlay,Union,Validategeometry,Fixgeometry}*`, ...) follow the same pattern: each field maps 1:1 onto the server schema, with snake_case Python names and camelCase aliases.

### Conditional importExport models
`importexport_conditional.py` ships 54 concrete `<Source>To<Target>StartParameters` classes (9 sources `csv` / `gdb` / `kml` / `tab` / `gpkg` / `excel` / `layer` / `shape` / `otherfile` x 6 targets `csv` / `gpkg` / `excel` / `layer` / `shape` / `geojson`), built from `<Source>SourceMixin` / `<Target>TargetMixin` mixins. Use them directly; the high-level [[Tasks/Import|Import]] / [[Tasks/Export|Export]] wrappers do exactly that. Every class also has an `ImportexportSource<Src>Target<Tgt>StartParameters` alias re-exported for backward compatibility.

```python
from evergis_tools.tasks.worker_models import (
    CsvToLayerStartParameters,
    LayerReferenceConfig,
)

params = CsvToLayerStartParameters(
    source_fileName="john_doe/.../charging.csv",
    source_columnDelimiter=",",
    source_coordSourceFields=["lon", "lat"],
    source_spatialReference=4326,
    target_layer=LayerReferenceConfig(name="john_doe.evg_csv_charging"),
)
```

The base `BaseImportexportStartParameters` (also exported) and `ImportexportStartParameters` (a `typing.Union` over all 54 combinations) are available for code that needs to accept any importExport variant.

## Key Behaviors

- **Generated, do not edit by hand.** `models.py` and `importexport_conditional.py` are regenerated from the server's worker task prototypes and overwritten on every regen. Server-side schema changes (new worker, new field) land here automatically. The generator derives common fields and `ChildrenFields` discriminators and emits Pydantic v2 models with enum-based lookup types.
- **camelCase aliases, snake_case attributes.** Every field is declared as `python_name: T = Field(None, alias='serverName')`; `populate_by_name = True` lets you build instances with either form. Serialisation always uses the server alias - safe to pass straight into `TaskPrototypeDto`.
- **All fields are `Optional`.** The generator does not have authoritative required/optional info from the server, so it marks everything `Optional[...] = None`. Validation of required fields happens server-side when the task runs; if you want stronger guarantees, wrap the model in a high-level helper (see `evergis_tools/tasks/import_tools/` for examples).
- **`proccessingType` typo is server-side.** Every `geoProcessing:*` and `netEngine:ODMatrix` / `availabilityArea` model carries a `proccessing_type` field with `alias='proccessingType'` (double "c"). This is the server contract; do not "fix" the alias - the request will be rejected.
- **`create_task_prototype` strips the subtype.** `task_type="geoProcessing:buffer"` is collapsed to `"geoProcessing"` before being placed in `SubTaskSettingsDto.type`. The subtype is encoded implicitly through the `*StartParameters` class you pass.

## See Also
- [[Tasks]] - execute the resulting `TaskPrototypeDto` with `TaskManager` / `run_task`
- [[Tasks/Import|Import]] - high-level `import_<format>_to_layer` wrappers that build conditional importExport params for you
- [[Tasks/Export|Export]] - the reverse direction (layer -> file)
- [[Tasks/Geoprocessing|Geoprocessing]] - copy / update / delete / union / validate / fix geometry tasks
- [[Tasks/Network|Network]] - batch isochrones and OD matrix (uses `Netengine*StartParameters`)
