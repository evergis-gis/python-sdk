"""High-level helper for geoProcessing:copy tasks using EQL as source."""

from __future__ import annotations

from typing import Callable, Dict, Optional

from evergis_api import Client

from ...catalog.resources import resolve_target_layer_parent
from ..models import TaskExecutionResult, TaskProgress
from ..pipeline import TaskStep
from ..utils import run_task
from ..worker_models import (
    GeoprocessingCopyStartParameters,
    LayerReferenceConfig,
    SourceEqlConfig,
    create_task_prototype,
)

DEFAULT_ID_ATTRIBUTE = "gid"
DEFAULT_GEOMETRY_ATTRIBUTE = "geometry"


def copy_layer_via_eql(
    client: Client,
    *,
    eql: str,
    target_layer: str,
    target_layer_alias: Optional[str] = None,
    target_layer_parent_path: Optional[str] = None,
    columns_mapping: Optional[Dict[str, str]] = None,
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
) -> "TaskExecutionResult | TaskStep":
    """Copy records returned by an EQL query into another layer via geoProcessing task.

    Args:
        client: Initialised EverGIS API client.
        eql: EQL query that defines the source dataset.
        target_layer: Name of the layer that will receive the copied features.
        target_layer_alias: Optional alias for the target layer when creating the task.
        target_layer_parent_path: Optional catalog path for parent folder (e.g., "john_doe:Projects/Data").
                                  If the path doesn't exist, all missing folders will be created automatically.
        columns_mapping: Optional mapping between source and target attribute names.
        source_condition: Optional additional condition applied on top of the EQL.
        source_id_attribute: Attribute name used as identifier in the source query (default: ``gid``).
        source_geometry_attribute: Attribute name that contains geometry in the source query (default: ``geometry``).
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

    Example:
        >>> from evergis_api import Client
        >>> from evergis_tools.tasks.geoprocessing import copy_layer_via_eql
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>>
        >>> # Copy layer to existing or new folder (automatically created)
        >>> result = copy_layer_via_eql(
        ...     client=client,
        ...     eql="SELECT * FROM source_layer",
        ...     target_layer="copied_layer",
        ...     target_layer_parent_path="john_doe:Projects/Layer copies"
        ... )
    """
    if not eql:
        raise ValueError("Parameter 'eql' must be provided and not empty.")
    if not target_layer:
        raise ValueError("Parameter 'target_layer' must be provided and not empty.")

    # Resolve parent folder ID for target layer
    target_layer_parent_id = resolve_target_layer_parent(
        client=client,
        target_layer=target_layer,
        target_layer_parent_path=target_layer_parent_path,
    )

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

    start_params = GeoprocessingCopyStartParameters(
        proccessingType="copy",
        source_layer=source_layer,
        target_layer=target_layer_config,
        columns_mapping=columns_mapping,
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

    # print(prototype.model_dump_json(indent=2))

    return run_task(
        client=client,
        prototype=prototype,
        wait_for_completion=wait_for_completion,
        timeout=timeout,
        check_interval=check_interval,
        progress_callback=progress_callback,
        log=log,
    )
