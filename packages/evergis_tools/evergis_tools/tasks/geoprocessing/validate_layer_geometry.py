"""High-level helper for geoProcessing:validateGeometry tasks."""

from __future__ import annotations

from typing import Callable, Optional

from evergis_api import Client

from ..models import TaskExecutionResult, TaskProgress
from ..pipeline import TaskStep
from ..utils import run_task
from ..worker_models import (
    GeoprocessingValidategeometryStartParameters,
    LayerReferenceConfig,
    SourceEqlConfig,
    create_task_prototype,
)

DEFAULT_ID_ATTRIBUTE = "gid"
DEFAULT_GEOMETRY_ATTRIBUTE = "geometry"


def validate_layer_geometry(
    client: Client,
    *,
    source_layer: str,
    target_layer: str,
    target_layer_alias: Optional[str] = None,
    target_layer_parent_id: Optional[str] = None,
    invalid_reason_column: str = "validation_error",
    base_object_id_attribute: str = "source_object_id",
    source_condition: Optional[str] = None,
    source_id_attribute: str = DEFAULT_ID_ATTRIBUTE,
    source_geometry_attribute: str = DEFAULT_GEOMETRY_ATTRIBUTE,
    materialized_view: bool = False,
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
    """Validate geometries in a layer or EQL query and write invalid records to target layer.

    This function can work with either a simple layer name or an EQL query as the source.
    Invalid geometries are written to the target layer along with the validation error reason.

    Args:
        client: Initialized EverGIS API client.
        source_layer: Source layer name or EQL query. Can be:
            - Layer name: ``"buildings"`` - validates all objects in the layer
            - EQL query: ``"SELECT * FROM buildings WHERE height > 100"`` - validates filtered objects
        target_layer: Name of the layer that will receive invalid geometry records.
        target_layer_alias: Optional alias for the target layer when creating the task.
        target_layer_parent_id: Optional parent source identifier for the target layer.
        invalid_reason_column: Attribute name for storing the validation error message (default: ``validation_error``).
        base_object_id_attribute: Attribute name for storing the ID of the source feature (default: ``source_object_id``).
        source_condition: Optional additional condition applied on top of the layer/EQL.
        source_id_attribute: Attribute name used as identifier in the source (default: ``gid``).
        source_geometry_attribute: Attribute name that contains geometry in the source (default: ``geometry``).
        materialized_view: Materialize view for complex EQL queries (default: False).
        enabled: Should the task prototype be enabled immediately (default: True).
        start_if_previous_error: Run even if previous execution ended with an error (default: True).
        start_if_previous_not_finished: Run if previous execution is still running (default: False).
        order: Execution order for the subtask inside the prototype (default: 0).
        wait_for_completion: Wait for task completion before returning (default: True).
        timeout: Timeout for waiting in seconds. ``None`` disables the timeout.
        check_interval: Interval between status checks when waiting (seconds).
        progress_callback: Optional custom callback to observe task progress.
        log: Verbose output (JSON prototype, execution statuses).

    Returns:
        TaskExecutionResult describing the task execution outcome or initial status when
        ``wait_for_completion`` is False.

    Examples:
        Validate all geometries in a layer::

            result = validate_layer_geometry(
                client,
                source_layer="buildings",
                target_layer="invalid_buildings"
            )

        Validate geometries in filtered data::

            result = validate_layer_geometry(
                client,
                source_layer="SELECT * FROM roads WHERE status='new'",
                target_layer="invalid_new_roads",
                invalid_reason_column="error_description"
            )

        Use with additional condition::

            result = validate_layer_geometry(
                client,
                source_layer="buildings",
                source_condition="created_date > '2024-01-01'",
                target_layer="invalid_recent_buildings"
            )
    """
    if not source_layer:
        raise ValueError("Parameter 'source_layer' must be provided and not empty.")
    if not target_layer:
        raise ValueError("Parameter 'target_layer' must be provided and not empty.")

    # Determine if source_layer is an EQL query or layer name
    # Simple heuristic: if it contains SELECT/FROM keywords, treat as EQL
    is_eql = any(keyword in source_layer.upper() for keyword in ["SELECT", "FROM"])

    if is_eql:
        source_layer_config = SourceEqlConfig(
            eql=source_layer,
            condition=source_condition,
            id_attribute=source_id_attribute,
            geometry_attribute=source_geometry_attribute,
        )
    else:
        source_layer_config = SourceEqlConfig(
            layer_name=source_layer,
            condition=source_condition,
            id_attribute=source_id_attribute,
            geometry_attribute=source_geometry_attribute,
        )

    target_layer_config = LayerReferenceConfig(
        name=target_layer,
        alias=target_layer_alias,
        parent_id=target_layer_parent_id,
    )

    # Build start parameters using the generated model from workers
    start_params = GeoprocessingValidategeometryStartParameters(
        proccessingType="validateGeometry",
        source_layer=source_layer_config,
        target_layer=target_layer_config,
        base_object_id_attribute_name=base_object_id_attribute,
        invalid_reason_column=invalid_reason_column,
        materialized_view=materialized_view,
    )

    # Create task prototype
    if defer:
        return TaskStep(
            task_type='geoProcessing',
            start_parameters=start_params.model_dump(by_alias=True, exclude_none=True),
            description=description,
            order=order,
        )

    prototype = create_task_prototype(
        "geoProcessing",
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
