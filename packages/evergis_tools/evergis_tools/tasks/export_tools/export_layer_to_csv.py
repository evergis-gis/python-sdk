"""High-level export of EverGIS layer to CSV format."""

from __future__ import annotations

from typing import Callable, Dict, Iterable, Optional

from evergis_api import Client

from evergis_tools.catalog.resources import resolve_resource
from evergis_tools.tasks.worker_models import (
    LayerToCsvStartParameters,
    SourceEqlConfig,
    create_task_prototype,
)

from ..models import TaskExecutionResult, TaskProgress
from ..pipeline import TaskStep
from ..utils import run_task
def export_layer_to_csv(
    client: Client,
    *,
    source_layer: str,
    source_eql: Optional[str] = None,
    source_layer_condition: Optional[str] = None,
    target_file_name: str,
    target_parent_path: Optional[str] = None,
    column_delimiter: str = ";",
    coord_source_fields: Optional[Iterable[str]] = None,
    spatial_reference: int = 4326,
    is_wkt: bool = False,
    attribute_name_row_number: Optional[int] = None,
    alias_row_number: Optional[int] = None,
    first_data_row_number: Optional[int] = None,
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
    """Export EverGIS layer to CSV file via ImportExport task.

    This function supports two export modes:
    1. Simple export - exports entire layer by specifying layer name
    2. EQL-based export - exports filtered data using EQL query

    Args:
        client: Initialized EverGIS API client.
        source_layer: Source layer name for export.
        source_eql: EQL query with all filters (optional). If provided, all conditions
            must be included in the query itself.
        source_layer_condition: Filter condition for layer without EQL (optional).
            Only used when source_eql is not provided.
        target_file_name: Resource ID or catalog path for target CSV file.
        target_parent_path: Parent folder catalog path (optional). If specified,
            the target file will be created/resolved in this folder.
        column_delimiter: Column delimiter character (default: ";").
        coord_source_fields: Coordinate field names for geometry layers (optional).
            Only applicable for geometry layers.
        spatial_reference: SRID for spatial data (default: 4326).
            Only applicable for geometry layers.
        is_wkt: Whether geometry should be exported in WKT format (default: False).
            Only applicable for geometry layers.
        attribute_name_row_number: Row number for attribute names (optional).
        alias_row_number: Row number for aliases (optional).
        first_data_row_number: First data row number (optional).
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
        >>> from evergis_tools.tasks.export_tools import export_layer_to_csv
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>>
        >>> result = export_layer_to_csv(
        ...     client=client,
        ...     source_layer="john_doe.my_layer",
        ...     target_file_name="export.csv",
        ...     target_parent_path="john_doe:Projects/Exports",
        ...     column_delimiter=","
        ... )

        Export with EQL filtering:

        >>> result = export_layer_to_csv(
        ...     client=client,
        ...     source_layer="john_doe.my_layer",
        ...     source_eql="SELECT * FROM john_doe.my_layer WHERE population > 1000",
        ...     target_file_name="filtered_export.csv",
        ...     target_parent_path="john_doe:Projects/Exports",
        ...     batch_count=50000
        ... )

        Export geometry layer with coordinate fields:

        >>> result = export_layer_to_csv(
        ...     client=client,
        ...     source_layer="john_doe.cities",
        ...     target_file_name="cities_export.csv",
        ...     target_parent_path="john_doe:Exports",
        ...     coord_source_fields=["lon", "lat"],
        ...     spatial_reference=4326
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

    # Prepare coordinate fields
    coord_fields = list(coord_source_fields) if coord_source_fields else None

    # Create start parameters
    start_params = LayerToCsvStartParameters(
        source_layer=source_layer_config,
        target_fileName=target_file_resource_id,
        target_columnDelimiter=column_delimiter,
        target_coordSourceFields=coord_fields,
        target_spatialReference=spatial_reference,
        target_isWkt=is_wkt,
        target_attributeNameRowNumber=attribute_name_row_number,
        target_aliasRowNumber=alias_row_number,
        target_firstDataRowNumber=first_data_row_number,
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
