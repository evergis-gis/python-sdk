"""High-level CSV import into an EverGIS layer."""

from __future__ import annotations

from typing import Callable, Dict, Iterable, Optional

from evergis_api import Client

from evergis_tools.catalog.resources import resolve_resource, resolve_target_layer_parent
from evergis_tools.tasks.worker_models import (
    CsvToLayerStartParameters,
    LayerReferenceConfig,
    create_task_prototype,
)

from ..models import TaskExecutionResult, TaskProgress
from ..pipeline import TaskStep
from ..utils import run_task
def import_csv_to_layer(
    client: Client,
    *,
    source_file_name: str,
    source_coord_fields: Iterable[str] = None,
    target_layer: str,
    target_layer_alias: Optional[str] = None,
    target_layer_parent_path: Optional[str] = None,
    column_delimiter: str = ";",
    spatial_reference: int = 4326,
    is_wkt: bool = False,
    contains_alias_row: bool = False,
    attribute_name_row_number: Optional[int] = None,
    alias_row_number: Optional[int] = None,
    first_data_row_number: Optional[int] = None,
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
    """Import a CSV file into an EverGIS layer via an ImportExport task.

    Args:
        client: Initialized EverGIS API client.
        source_file_name: Catalog path, resource ID, or system name of CSV file.
        source_coord_fields: Names of the coordinate fields.
        target_layer: Target layer name.
        target_layer_alias: Target layer alias (optional).
        target_layer_parent_path: Path to the parent folder in the catalog (e.g., "john_doe:Projects/Data").
        column_delimiter: Column delimiter (default `;`).
        spatial_reference: SRID of the source data (default 4326).
        is_wkt: Flag set if the CSV contains geometry in WKT.
        contains_alias_row: Whether the CSV has an alias row.
        attribute_name_row_number: Row number with attribute names (optional).
        alias_row_number: Row number with aliases (optional).
        first_data_row_number: Number of the first data row (optional).
        attribute_mapping: Mapping of input fields to target names.
        attribute_type_mapping: Mapping of field types.
        default_values: Default values for fields (optional).
        enabled: Whether to enable the prototype after creation.
        start_if_previous_error: Whether to start on a previous task error.
        start_if_previous_not_finished: Whether to start if the previous task is not finished.
        order: Subtask order.
        wait_for_completion: Whether to wait for execution completion.
        timeout: Waiting timeout (seconds).
        batch_count: Server-side import/export batch size (rows per batch);
            ``None`` lets the worker decide.
        check_interval: Status polling interval (seconds).
        progress_callback: Custom progress callback.
        log: Verbose output (JSON prototype, execution statuses).

    Returns:
        TaskExecutionResult with the final execution status.
    """
    # Resolve source file path to resource_id if needed
    source_resource = resolve_resource(client, source_file_name)
    source_file_resource_id = source_resource.resourceId

    if source_coord_fields:
        coord_fields = list(source_coord_fields)
        # ``attribute_mapping`` defaults to None - guard the merge so building
        # geometry from coordinate columns works without an explicit mapping.
        attribute_mapping = {"geometry": "geometry"} | (attribute_mapping or {})
    else:
        coord_fields = None

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

    start_params = CsvToLayerStartParameters(
        source_fileName=source_file_resource_id,
        source_coordSourceFields=coord_fields,
        source_columnDelimiter=column_delimiter,
        source_spatialReference=spatial_reference,
        source_isWkt=is_wkt,
        source_containsAliasRow=contains_alias_row,
        source_attributeNameRowNumber=attribute_name_row_number,
        source_aliasRowNumber=alias_row_number,
        source_firstDataRowNumber=first_data_row_number,
        target_layer=target_layer_config,
        attribute_mapping=attribute_mapping,
        attribute_type_mapping=attribute_type_mapping,
        default_values=default_values,
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
