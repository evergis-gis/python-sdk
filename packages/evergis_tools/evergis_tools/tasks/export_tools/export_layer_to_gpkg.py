"""High-level export of EverGIS layer to GeoPackage (GPKG) format."""

from __future__ import annotations

from typing import Callable, Dict, Optional

from evergis_api import Client

from evergis_tools.catalog.resources import resolve_resource
from evergis_tools.tasks.worker_models import (
    LayerToGpkgStartParameters,
    SourceEqlConfig,
    create_task_prototype,
)

from ..models import TaskExecutionResult, TaskProgress
from ..pipeline import TaskStep
from ..utils import run_task


def export_layer_to_gpkg(
    client: Client,
    *,
    source_layer: str,
    source_eql: Optional[str] = None,
    source_layer_condition: Optional[str] = None,
    target_file_name: str,
    target_parent_path: Optional[str] = None,
    target_layer_name: Optional[str] = None,
    attribute_mapping: Optional[Dict[str, str]] = None,
    attribute_type_mapping: Optional[Dict[str, str]] = None,
    default_values: Optional[Dict[str, str]] = None,
    batch_count: int = 50000,
    enabled: bool = True,
    start_if_previous_error: bool = True,
    start_if_previous_not_finished: bool = False,
    order: Optional[int] = None,
    description: Optional[str] = None,
    wait_for_completion: bool = True,
    timeout: Optional[float] = 300,
    check_interval: float = 2.0,
    progress_callback: Optional[Callable[[TaskProgress], None]] = None,
    log: bool = False,
    defer: bool = False,
) -> "TaskExecutionResult | TaskStep":
    """Export an EverGIS layer to a GeoPackage file via the ImportExport task.

    GPKG is a SQLite-based container that holds one or more layers. The
    server creates the file at ``target_parent_path/target_file_name``
    and writes the layer under ``target_layer_name`` (defaults to the
    source layer name if not provided).

    Args:
        client: Initialized EverGIS API client.
        source_layer: Source layer name for export.
        source_eql: EQL query with all filters baked in (optional). If
            provided, ``source_layer_condition`` is ignored.
        source_layer_condition: Additional WHERE applied to the source
            layer when ``source_eql`` is not provided.
        target_file_name: Output file name (e.g. ``my_export.gpkg``)
            when ``target_parent_path`` is used, or a full catalog path /
            resource id otherwise.
        target_parent_path: Catalog path of the parent folder for the
            output file. When given, the file is created here.
        target_layer_name: Layer name inside the GPKG container
            (default: same as ``source_layer``).
        attribute_mapping: ``{source_field: target_field}`` rename map.
        attribute_type_mapping: ``{field: EverGISType}`` type overrides.
        default_values: ``{field: value}`` default values.
        batch_count: Streaming batch size (default 50000).
        enabled / start_if_previous_error / start_if_previous_not_finished
            / order / description: Prototype scheduling knobs.
        wait_for_completion: Block until the task finishes (default True).
        timeout: Wait timeout in seconds (``None`` disables).
        check_interval: Status polling interval in seconds.
        progress_callback: Custom progress callback.
        log: Verbose output (JSON prototype, execution statuses).

    Returns:
        TaskExecutionResult with the final execution status.
    """
    if not source_layer:
        raise ValueError("Parameter 'source_layer' must be provided and not empty.")
    if not target_file_name:
        raise ValueError("Parameter 'target_file_name' must be provided and not empty.")

    if target_parent_path:
        resolve_resource(client, target_parent_path)
        target_file_resource_id = target_file_name
    else:
        target_resource = resolve_resource(client, target_file_name)
        target_file_resource_id = target_resource.resourceId

    if source_eql:
        source_layer_config = SourceEqlConfig(eql=source_eql)
    else:
        source_layer_config = SourceEqlConfig(
            layer_name=source_layer,
            condition=source_layer_condition,
        )

    start_params = LayerToGpkgStartParameters(
        source_layer=source_layer_config,
        target_fileName=target_file_resource_id,
        # target_layerName=target_layer_name,
        attribute_mapping=attribute_mapping,
        attribute_type_mapping=attribute_type_mapping,
        default_values=default_values,
        batch_count=batch_count,
    )

    if defer:
        return TaskStep(
            task_type="importExport",
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
