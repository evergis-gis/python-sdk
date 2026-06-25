"""High-level export of EverGIS layer to GeoJSON format."""

from __future__ import annotations

from typing import Callable, Dict, Optional

from evergis_api import Client

from evergis_tools.catalog.resources import resolve_resource
from evergis_tools.tasks.worker_models import (
    LayerToGeojsonStartParameters,
    SourceEqlConfig,
    create_task_prototype,
)

from ..models import TaskExecutionResult, TaskProgress
from ..pipeline import TaskStep
from ..utils import run_task
def export_layer_to_geojson(
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
    """Export EverGIS layer to GeoJSON format via ImportExport task.

    This function supports two export modes:
    1. Simple export - exports entire layer by specifying layer name
    2. EQL-based export - exports filtered data using EQL query

    GeoJSON is a geospatial data format based on JSON that natively supports geometry,
    so coordinate field parameters are not required.

    Args:
        client: Initialized EverGIS API client.
        source_layer: Source layer name for export.
        source_eql: EQL query with all filters (optional). If provided, all conditions
            must be included in the query itself.
        source_layer_condition: Filter condition for layer without EQL (optional).
            Only used when source_eql is not provided.
        target_file_name: Resource ID or catalog path for target GeoJSON file.
        target_parent_path: Parent folder catalog path (optional). If specified,
            the target file will be created/resolved in this folder.
        target_layer_name: Name of the layer within the GeoJSON file (optional).
            If not specified, defaults to the source layer name.
        attribute_mapping: Dictionary mapping source field names to target field names.
        attribute_type_mapping: Dictionary mapping field names to their target types.
        default_values: Dictionary of default values for fields.
        batch_count: Batch size for export processing (default: 50000).
        enabled: Enable task prototype after creation (default: True).
        start_if_previous_error: Start task even if previous task failed (default: True).
        start_if_previous_not_finished: Start task if previous task not finished (default: False).
        order: Subtask execution order (default: 0).
        wait_for_completion: Wait for task completion before returning (default: True).
        timeout: Wait timeout in seconds (default: 300). None disables timeout.
        check_interval: Status check interval in seconds (default: 2.0).
        progress_callback: Custom progress callback function.
        log: Verbose output (JSON prototype, execution statuses).

    Returns:
        TaskExecutionResult with final execution status.

    Raises:
        ValueError: If layer name or target file name is empty.
        TimeoutError: If task exceeds timeout duration.

    Example:
        Simple export of entire layer:

        >>> from evergis_api import Client
        >>> from evergis_tools.tasks.export_tools import export_layer_to_geojson
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>>
        >>> result = export_layer_to_geojson(
        ...     client=client,
        ...     source_layer="john_doe.my_layer",
        ...     target_file_name="export.geojson",
        ...     target_parent_path="john_doe:Projects/Exports"
        ... )

        Export with EQL filtering:

        >>> result = export_layer_to_geojson(
        ...     client=client,
        ...     source_layer="john_doe.my_layer",
        ...     source_eql="SELECT * FROM john_doe.my_layer WHERE type = 'point'",
        ...     target_file_name="points_export.geojson",
        ...     target_parent_path="john_doe:Projects/Exports",
        ...     target_layer_name="filtered_points"
        ... )

        Export with attribute mapping:

        >>> result = export_layer_to_geojson(
        ...     client=client,
        ...     source_layer="john_doe.roads",
        ...     target_file_name="roads_export.geojson",
        ...     target_parent_path="john_doe:Exports",
        ...     attribute_mapping={
        ...         "gid": "id",
        ...         "road_name": "name",
        ...         "road_type": "type",
        ...         "geometry": "geometry"
        ...     },
        ...     batch_count=75000
        ... )
    """
    if not source_layer:
        raise ValueError("Parameter 'source_layer' must be provided and not empty.")
    if not target_file_name:
        raise ValueError("Parameter 'target_file_name' must be provided and not empty.")

    # Resolve target file resource
    if target_parent_path:
        # Resolve parent folder (ensures it exists)
        resolve_resource(client, target_parent_path)
        target_file_resource_id = target_file_name
    else:
        target_resource = resolve_resource(client, target_file_name)
        target_file_resource_id = target_resource.resourceId

    # Build source layer configuration
    # Always use SourceEqlConfig (not a simple string)
    if source_eql:
        # EQL-based export: only eql parameter (layer name is in the query)
        source_layer_config = SourceEqlConfig(
            eql=source_eql,
        )
    else:
        # Simple layer export: use layer_name and condition parameters
        source_layer_config = SourceEqlConfig(
            layer_name=source_layer,
            condition=source_layer_condition,
        )

    # Create start parameters
    start_params = LayerToGeojsonStartParameters(
        source_layer=source_layer_config,
        target_fileName=target_file_resource_id,
        target_layerName=target_layer_name,
        attribute_mapping=attribute_mapping,
        attribute_type_mapping=attribute_type_mapping,
        default_values=default_values,
        batch_count=batch_count,
    )

    # Create task prototype
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

    # Run task
    return run_task(
        client=client,
        prototype=prototype,
        wait_for_completion=wait_for_completion,
        timeout=timeout,
        check_interval=check_interval,
        progress_callback=progress_callback,
        log=log,
    )
