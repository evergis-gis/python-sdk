"""High-level Shapefile import to EverGIS layer."""

from __future__ import annotations

from typing import Callable, Dict, Optional

from evergis_api import Client

from evergis_tools.catalog.resources import resolve_resource, resolve_target_layer_parent
from evergis_tools.tasks.worker_models import (
    ImportexportSourceOtherfileTargetLayerStartParameters,
    LayerReferenceConfig,
    create_task_prototype,
)

from evergis_tools.tasks.models import TaskExecutionResult, TaskProgress
from evergis_tools.tasks.pipeline import TaskStep
from evergis_tools.tasks.utils import run_task
def import_shapefile_to_layer(
    client: Client,
    *,
    source_file_name: str,
    target_layer: str,
    target_layer_alias: Optional[str] = None,
    target_layer_parent_path: Optional[str] = None,
    source_layer_name: Optional[str] = None,
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
    """Import Shapefile (ZIP) to EverGIS layer via ImportExport task.

    Args:
        client: Initialized EverGIS API client.
        source_file_name: Catalog path, resource ID, or system name of Shapefile ZIP archive.
        target_layer: Target layer name/path (e.g., ``project.layer``).
        target_layer_alias: Target layer alias (optional).
        target_layer_parent_path: Optional catalog path for parent folder (e.g., "john_doe:Projects/Data").
                                  If the path doesn't exist, all missing folders will be created automatically.
        source_layer_name: Layer name inside the archive (optional, for multi-layer archives).
        attribute_mapping: Mapping of input fields to target names.
        attribute_type_mapping: Mapping of target attribute types.
        enabled: Enable prototype immediately after creation.
        start_if_previous_error: Allow start after previous execution error.
        start_if_previous_not_finished: Allow start if previous task is still running.
        order: Subtask order in prototype.
        wait_for_completion: Wait for execution completion.
        timeout: Waiting timeout (seconds). ``None`` disables timeout.
        batch_count: Server-side import/export batch size (rows per batch);
            ``None`` lets the worker decide.
        check_interval: Status polling interval (seconds).
        progress_callback: Custom progress callback.
        log: Verbose output (JSON prototype, execution statuses).

    Returns:
        TaskExecutionResult with final execution status.

    Example:
        >>> from evergis_api import Client
        >>> from evergis_tools.tasks.import_tools import import_shapefile_to_layer
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>>
        >>> # Import shapefile to existing or new folder (automatically created)
        >>> result = import_shapefile_to_layer(
        ...     client=client,
        ...     source_file_name="shapefile.zip",
        ...     target_layer="imported_layer",
        ...     source_layer_name="layer_in_zip",
        ...     target_layer_parent_path="john_doe:Projects/Imports"
        ... )
    """

    if not source_file_name:
        raise ValueError("Parameter 'source_file_name' must be provided and not empty.")
    if not target_layer:
        raise ValueError("Parameter 'target_layer' must be provided and not empty.")
    if not source_layer_name:
        raise ValueError("Parameter 'source_layer_name' must be provided and not empty.")

    # Resolve source file path to resource_id if needed
    source_resource = resolve_resource(client, source_file_name)
    source_file_resource_id = source_resource.resourceId

    # Resolve parent folder ID for target layer
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

    start_params = ImportexportSourceOtherfileTargetLayerStartParameters(
        source_fileName=source_file_resource_id,
        source_layerName=source_layer_name if source_layer_name else None,
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
