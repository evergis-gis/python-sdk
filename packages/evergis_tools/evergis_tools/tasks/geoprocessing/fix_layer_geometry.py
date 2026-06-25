"""High-level helper for geoProcessing:fixGeometry tasks."""

from __future__ import annotations

from typing import Callable, Optional

from evergis_api import Client

from ..models import TaskExecutionResult, TaskProgress
from ..pipeline import TaskStep
from ..utils import run_task
from ..worker_models import (
    GeoprocessingFixgeometryStartParameters,
    LayerReferenceConfig,
    create_task_prototype,
)


def fix_layer_geometry(
    client: Client,
    *,
    layer_name: str,
    enabled: bool = True,
    start_if_previous_error: bool = True,
    start_if_previous_not_finished: bool = False,
    order: Optional[int] = None,
    description: Optional[str] = None,
    wait_for_completion: bool = True,
    timeout: Optional[float] = 600,
    check_interval: float = 2.0,
    progress_callback: Optional[Callable[[TaskProgress], None]] = None,
    log: bool = False,
    defer: bool = False,
) -> "TaskExecutionResult | TaskStep":
    """Fix invalid geometries in a layer (in-place operation).

    This function repairs invalid geometries directly in the specified layer
    using standard geometry fixing algorithms (such as buffer(0) or make_valid).
    The operation modifies geometries in place without creating a new layer.

    Args:
        client: Initialized EverGIS API client.
        layer_name: Name of the layer to fix geometries in.
        enabled: Should the task prototype be enabled immediately (default: True).
        start_if_previous_error: Run even if previous execution ended with an error (default: True).
        start_if_previous_not_finished: Run if previous execution is still running (default: False).
        order: Execution order for the subtask inside the prototype (default: 0).
        wait_for_completion: Wait for task completion before returning (default: True).
        timeout: Timeout for waiting in seconds. ``None`` disables the timeout.
            Default is 600 seconds (10 minutes) as this can be a long-running operation.
        check_interval: Interval between status checks when waiting (seconds).
        progress_callback: Optional custom callback to observe task progress.
        log: Verbose output (JSON prototype, execution statuses).

    Returns:
        TaskExecutionResult describing the task execution outcome or initial status when
        ``wait_for_completion`` is False.

    Examples:
        Fix all invalid geometries in a layer::

            result = fix_layer_geometry(
                client,
                layer_name="buildings"
            )

        Fix geometries with extended timeout for large layers::

            result = fix_layer_geometry(
                client,
                layer_name="large_polygons",
                timeout=900  # 15 minutes
            )

        Start fix operation without waiting for completion::

            result = fix_layer_geometry(
                client,
                layer_name="roads",
                wait_for_completion=False
            )
            # Check status later...

    Notes:
        - This is an **in-place** operation that modifies the original layer
        - Cannot be used with EQL queries (only with layer names)
        - Typically used after ``validate_layer_geometry`` to automatically fix issues
        - May take significant time for layers with many or complex geometries
    """
    if not layer_name:
        raise ValueError("Parameter 'layer_name' must be provided and not empty.")

    target_layer_config = LayerReferenceConfig(
        name=layer_name,
    )

    # Build start parameters using the generated model from workers
    start_params = GeoprocessingFixgeometryStartParameters(
        target_layer=target_layer_config,
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
        "geoProcessing:fixGeometry",
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
