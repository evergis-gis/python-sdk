"""High-level helper for geoProcessing:update tasks using an EQL query as the source."""

from __future__ import annotations

from typing import Callable, Optional

from evergis_api import Client

from ..models import TaskExecutionResult, TaskProgress
from ..pipeline import TaskStep
from ..utils import run_task
from ..worker_models import (
    GeoprocessingUpdateStartParameters,
    LayerReferenceConfig,
    SourceEqlConfig,
    create_task_prototype,
)

DEFAULT_ID_ATTRIBUTE = "gid"
DEFAULT_GEOMETRY_ATTRIBUTE = "geometry"


def update_layer_via_eql(
    client: Client,
    *,
    eql: str,
    target_layer: str,
    target_layer_alias: Optional[str] = None,
    target_layer_parent_id: Optional[str] = None,
    source_condition: Optional[str] = None,
    source_id_attribute: str = DEFAULT_ID_ATTRIBUTE,
    source_geometry_attribute: str = DEFAULT_GEOMETRY_ATTRIBUTE,
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
    cached: bool = True,
) -> "TaskExecutionResult | TaskStep":
    """Update an EverGIS layer with features returned by an EQL query.

    Args:
        client: Initialised EverGIS API client instance.
        eql: EQL query that defines the update source dataset.
        target_layer: Name of the layer that will be updated.
        target_layer_alias: Optional alias for the target layer in task settings.
        target_layer_parent_id: Optional parent source identifier for the target layer.
        source_condition: Optional condition appended to the source definition.
        source_id_attribute: Identifier attribute present in the source (default: ``gid``).
        source_geometry_attribute: Geometry attribute used for the update (default: ``geometry``).
        enabled: Whether the created task prototype should be enabled immediately.
        start_if_previous_error: Allow execution if previous run finished with error.
        start_if_previous_not_finished: Allow execution when previous run is not finished yet.
        order: Execution order of the subtask inside the prototype.
        wait_for_completion: Wait for task completion before returning.
        timeout: Timeout (seconds) for waiting; ``None`` disables timeout.
        check_interval: Interval (seconds) between status checks while waiting.
        progress_callback: Custom callback invoked with task progress updates.
        log: Verbose output (JSON prototype, execution statuses).

    Returns:
        TaskExecutionResult describing the task execution outcome or initial status when
        ``wait_for_completion`` is False.
    """
    if not eql:
        raise ValueError("Parameter 'eql' must be provided and not empty.")
    if not target_layer:
        raise ValueError("Parameter 'target_layer' must be provided and not empty.")

    source_layer = SourceEqlConfig(
        eql=eql,
        condition=source_condition,
        id_attribute=source_id_attribute,
        geometry_attribute=source_geometry_attribute,
    )

    target_layer_config = LayerReferenceConfig(
        name=target_layer,
        alias=target_layer_alias,
        parent_id=target_layer_parent_id,
    )

    start_params = GeoprocessingUpdateStartParameters(
        proccessingType="update",
        source_layer=source_layer,
        target_layer=target_layer_config,
        materializedView=cached,
    )

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
    # print (prototype.model_dump_json(indent=2))
    return run_task(
        client=client,
        prototype=prototype,
        wait_for_completion=wait_for_completion,
        timeout=timeout,
        check_interval=check_interval,
        progress_callback=progress_callback,
        log=log,
    )
