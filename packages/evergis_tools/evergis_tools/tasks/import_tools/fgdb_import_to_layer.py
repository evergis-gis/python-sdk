"""High-level File Geodatabase (FGDB / .gdb) import to EverGIS layer."""

from __future__ import annotations

from typing import Callable, Dict, Optional

from evergis_api import Client

from evergis_tools.catalog.resources import resolve_resource, resolve_target_layer_parent
from evergis_tools.tasks.worker_models import (
    ImportexportSourceGdbTargetLayerStartParameters,
    LayerReferenceConfig,
    create_task_prototype,
)

from evergis_tools.tasks.models import TaskExecutionResult, TaskProgress
from evergis_tools.tasks.pipeline import TaskStep
from evergis_tools.tasks.utils import run_task
def import_fgdb_to_layer(
    client: Client,
    *,
    source_file_name: str,
    source_layer_name: str,
    target_layer: str,
    target_layer_alias: Optional[str] = None,
    target_layer_parent_path: Optional[str] = None,
    attribute_mapping: Optional[Dict[str, str]] = None,
    attribute_type_mapping: Optional[Dict[str, str]] = None,
    default_values: Optional[Dict[str, str]] = None,
    enabled: bool = True,
    start_if_previous_error: bool = True,
    start_if_previous_not_finished: bool = False,
    order: Optional[int] = None,
    description: Optional[str] = None,
    wait_for_completion: bool = True,
    timeout: Optional[float] = 300,
    batch_count: Optional[int] = None,
    check_interval: float = 2.0,
    progress_callback: Optional[Callable[[TaskProgress], None]] = None,
    log: bool = False,
    defer: bool = False,
) -> "TaskExecutionResult | TaskStep":
    """Import one layer of a File Geodatabase (FGDB) into an EverGIS layer.

    A FGDB archive is a container - every call imports a single
    ``source_layer_name``. Iterate over multiple layers in the caller to
    load the whole file. Mirrors :func:`import_gpkg_to_layer`: the FGDB
    archive is uploaded once as a ``.gdb.zip`` File resource, then any
    number of import jobs target individual feature classes.

    Args:
        client: Initialized EverGIS API client.
        source_file_name: Catalog path / resource ID / system name of the
            FGDB archive already uploaded to EverGIS (typically a
            ``.gdb.zip`` File).
        source_layer_name: Feature class name inside the geodatabase.
        target_layer: Target layer name (e.g. ``project.layer``).
        target_layer_alias: Display name for the target layer.
        target_layer_parent_path: Catalog path of the destination folder
            (auto-creates missing folders).
        attribute_mapping: ``{source_field: target_field}``. Use
            :func:`build_attribute_mappings_from_schema` to derive an
            identity mapping straight from the server schema.
        attribute_type_mapping: ``{field: EverGISType}`` (e.g. ``Int32``,
            ``Double``, ``Point``).
        default_values: Default values for fields missing in the source.
        enabled: Enable prototype after creation.
        start_if_previous_error: Allow start after previous error.
        start_if_previous_not_finished: Allow start while previous run
            is still active.
        order: Subtask order in the prototype.
        description: Prototype description.
        wait_for_completion: Block until the run finishes.
        timeout: Wait timeout in seconds (``None`` disables).
        batch_count: Server-side import/export batch size (rows per batch);
            ``None`` lets the worker decide.
        check_interval: Status polling interval in seconds.
        progress_callback: Custom progress callback.
        log: Verbose output.

    Returns:
        TaskExecutionResult with the final execution status.
    """
    if not source_file_name:
        raise ValueError("Parameter 'source_file_name' must be provided and not empty.")
    if not source_layer_name:
        raise ValueError("Parameter 'source_layer_name' must be provided and not empty.")
    if not target_layer:
        raise ValueError("Parameter 'target_layer' must be provided and not empty.")

    source_resource = resolve_resource(client, source_file_name)
    source_file_resource_id = source_resource.resourceId

    target_layer_parent_id = resolve_target_layer_parent(
        client=client,
        target_layer=target_layer,
        target_layer_parent_path=target_layer_parent_path,
    )

    target_layer_config = LayerReferenceConfig(
        name=target_layer,
        alias=target_layer_alias,
        parentId=target_layer_parent_id,
    )

    start_params = ImportexportSourceGdbTargetLayerStartParameters(
        source_fileName=source_file_resource_id,
        source_layerName=source_layer_name,
        target_layer=target_layer_config,
        attributeMapping=attribute_mapping,
        attributeTypeMapping=attribute_type_mapping,
        defaultValues=default_values,
        batch_count=batch_count,
    )

    if defer:
        return TaskStep(
            task_type='importExport',
            start_parameters=start_params.model_dump(by_alias=True, exclude_none=True),
            description=description,
            order=order,
        )

    prototype = create_task_prototype(
        "importExport:importExport",
        start_parameters=start_params.model_dump(by_alias=True, exclude_none=True),
        enabled=enabled,
        start_if_previous_error=start_if_previous_error,
        start_if_previous_not_finished=start_if_previous_not_finished,
        order=order,
        description=description,
    )

    return run_task(
        client=client,
        prototype=prototype,
        wait_for_completion=wait_for_completion,
        timeout=timeout,
        check_interval=check_interval,
        progress_callback=progress_callback,
        log=log,
    )
