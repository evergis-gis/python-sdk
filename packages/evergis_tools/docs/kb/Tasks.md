---
title: Tasks
module: evergis_tools.tasks
---

# Tasks

Server-side async task execution with progress monitoring, plus category-specific wrappers (import / export / geoprocessing / network) on top of the shared `TaskManager`. Import: `from evergis_tools.tasks import ...`

## Subpackages

- [[Tasks/Import|Import]] - CSV / XLSX / Shapefile / GPKG / FGDB `File` resource -> EverGIS layer via the `importExport` worker.
- [[Tasks/Export|Export]] - layer (or EQL slice) -> CSV / XLSX / Shapefile / GPKG / GeoJSON `File` resource via the `importExport` worker.
- [[Tasks/Geoprocessing|Geoprocessing]] - copy / update / delete / union features through an EQL source, plus geometry validate / fix.
- [[Tasks/Network|Network]] - batch `netEngine` tasks: `build_isochrones`, `build_od_matrix` for whole layers at once.
- [[Tasks/WorkerModels|WorkerModels]] - auto-generated Pydantic `*StartParameters` models for every worker (`netEngine`, `geoProcessing`, `importExport`, `geocodeTask`, ...).

## Core API

Two entry points handle the lifecycle (create prototype -> start -> poll -> collect `TaskExecutionResult`):

- **`TaskManager(client)`** - main orchestrator. `create_and_run(task, wait_for_completion=True, wait_options=None, log=False)` is the canonical call. Also exposes `create_prototype`, `start_task`, `wait_for_completion`, `get_task_status`, `stop_task`, `get_prototypes`, `get_tasks_for_prototype`, `update_prototype_schedule`, `delete_prototype`, `set_prototype_enabled`, `start_task_with_id`, `get_task_resource`, `get_task_subtasks`, `get_active_workers`, `get_worker`, `run_worker_method`.
- **`run_task(client, prototype, *, wait_for_completion=True, timeout=300, check_interval=2.0, progress_callback=None, raise_on_failure=True, log=False)`** - one-shot convenience that builds a `TaskManager` internally and assembles `TaskWaitOptions`. Use it when you don't need the manager for anything else.

> **Warning:** A task that finishes in a failed state (`status` ERROR / INTERRUPTED / TIMEOUT) raises `TaskFailedError` by default - it does **not** return a result that looks like success. The exception carries the full result on `exc.result` (`status`, `error_message`, `subtasks`). Pass `raise_on_failure=False` (on the wrapper, `run_task`, or `TaskWaitOptions`) to get the failed `TaskExecutionResult` back instead and branch on `result.is_failed` yourself. Submit-time HTTP errors still raise `ApiClientError` as before.

> **Warning:** `stop_task(task_id)`, `update_prototype_schedule(prototype_id, schedule_options)`, `delete_prototype(prototype_id)`, and `set_prototype_enabled(prototype_id, enabled)` return `None` and raise `ApiClientError` when the server rejects the request - they no longer return a `bool` success flag. Do not branch on their return value; wrap the call in `try/except ApiClientError` to handle failure.

> **Note:** During `wait_for_completion`, an exception raised inside `progress_callback` is caught and logged via `logging.warning` (with traceback) - it does not stop the poll loop or fail the task.

The subpackage wrappers (`import_tools.import_csv_to_layer`, `export_tools.export_layer_to_gpkg`, `geoprocessing.copy_layer_via_eql`, `network.build_isochrones`, ...) build a worker prototype and submit it via `run_task`, returning the same `TaskExecutionResult`. They expose the wait knobs as flat kwargs (`wait_for_completion`, `timeout`, `check_interval`, `progress_callback`, `log`) - **not** a `wait_options=` object. Reach for `TaskManager` directly only when driving a raw prototype (custom worker, scheduling, manual prototype id):

```python
from evergis_tools import Client
from evergis_tools.tasks import create_progress_callback
from evergis_tools.tasks.import_tools import import_csv_to_layer

with Client() as client:
    result = import_csv_to_layer(
        client=client,
        source_file_name=f"{user}/.../source_files/data.csv",
        target_layer=f"{user}.evg_csv_demo",
        target_layer_parent_path=f"{user}/.../import/results",
        timeout=300,
        check_interval=2.0,
        progress_callback=create_progress_callback(),
    )
    print(result.is_successful, result.duration, result.error_message)
```

## Multi-step pipelines

`TaskPipeline` / `TaskStep` / `create_task_prototype_multi` chain several worker calls into a single server-side prototype carrying multiple `SubTaskSettingsDto` entries. Each subpackage wrapper accepts `defer=True` to return a `TaskStep` instead of running immediately; collect the steps in a `TaskPipeline`, then `run(client)` once.

`TaskStep.order` controls execution: `None` (default) means the server runs subtasks in parallel; an integer means strict ascending order. `TaskPipeline` is constructed without a client; the client is passed to `.run(...)`.

```python
from evergis_tools.tasks import TaskPipeline
from evergis_tools.tasks.geoprocessing import copy_layer_via_eql, validate_layer_geometry

step1 = copy_layer_via_eql(client, ..., defer=True)
step2 = validate_layer_geometry(client, ..., defer=True)
result = TaskPipeline(description="copy + validate").add(step1).add(step2).run(client)
```

`TaskPipeline.add_subtask(task_type, start_parameters, ...)` builds a `TaskStep` inline for raw worker payloads. `.build()` materialises a `TaskPrototypeDto` without submitting it.

## Models

| Model | Purpose |
|-------|---------|
| `TaskExecutionResult` | Return value of every wrapper. Fields: `task_id`, `prototype_id`, `status`, `started`, `ended`, `duration`, `subtasks`, `error_message`, `results`. Plus `is_successful` / `is_failed` / `is_running` properties driven by `RemoteTaskStatus`. |
| `TaskProgress` | Snapshot passed to `progress_callback`. Fields: `task_id`, `overall_progress` (0-100), `current_subtask`, `current_subtask_id`, `subtask_progress` (0-100), `status`, `message`, `processed_count`, `total_count`, `error_message`. Plus `is_running` property. |
| `TaskWaitOptions` | Polling config: `timeout` (s, optional), `check_interval` (s, default `2.0`), `progress_callback`, `raise_on_failure` (default `True`). |
| `TaskFailedError` | Raised by `wait_for_completion` (and thus every wrapper) when a task ends failed and `raise_on_failure` is set. Subclass of `RuntimeError`; carries the `TaskExecutionResult` on `.result`. |
| `TaskFilter` | Server-side filter for task listings: `user`, `status`, `created_after`, `created_before`, `skip` (default `0`), `take` (default `50`), `order_by`, `desc` (default `True`). |
| `ScheduleOptions` | Scheduled execution config: `schedule` (cron, validated as 5 or 6 fields), `delay_date`, `enabled` (default `True`), `start_if_previous_error` (default `False`), `start_if_previous_not_finished` (default `False`). |

Progress callback helpers: `create_progress_callback(check_interval=2.0)` (status + counters + elapsed seconds) and `create_simple_progress_callback()` (status + counters, no elapsed). Both consume `TaskProgress` and print one line per poll.

## See Also

- [[GeoTools]] - single-shape synchronous worker REST calls (one isochrone, one route in-process); use this module for batch task pipelines instead.
- [[Layers]] - target layers for import / geoprocessing / network tasks.
- [[Catalog/TaskResources|Task Resources]] - persisted task configurations in the catalog.
- [[Home]]
