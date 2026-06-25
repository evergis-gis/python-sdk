"""Helpers for EverGIS origin-destination matrix (ODMatrix) tasks."""

from __future__ import annotations

from typing import Any, Callable, Dict, Optional

from evergis_api import Client

from ..models import TaskExecutionResult, TaskProgress
from ..pipeline import TaskStep
from ..utils import run_task
from ..worker_models import (
    LayerReferenceConfig,
    NetengineOdmatrixStartParameters,
    SourceEqlConfig,
    create_task_prototype,
)

DEFAULT_SOURCE_ID_ATTRIBUTE = "gid"
DEFAULT_SOURCE_GEOMETRY_ATTRIBUTE = "geometry"
DEFAULT_ID_ATTRIBUTE_NAME = "gid"
DEFAULT_ID_FROM_ATTRIBUTE_NAME = "from"
DEFAULT_ID_TO_ATTRIBUTE_NAME = "to"
DEFAULT_TRANSPORT_TYPE_ATTRIBUTE_NAME = "transport_type"
DEFAULT_WEIGHT_PARAMETER_ATTRIBUTE_NAME = "weight_parameter"
DEFAULT_DISTANCE_ATTRIBUTE_NAME = "distance"


def build_od_matrix(
    client: Client,
    *,
    target_layer: str,
    source_from_layer_eql: Optional[str] = None,
    source_from_layer_name: Optional[str] = None,
    source_from_condition: Optional[str] = None,
    source_from_id_attribute: str = DEFAULT_SOURCE_ID_ATTRIBUTE,
    source_from_geometry_attribute: str = DEFAULT_SOURCE_GEOMETRY_ATTRIBUTE,
    source_to_layer_eql: Optional[str] = None,
    source_to_layer_name: Optional[str] = None,
    source_to_condition: Optional[str] = None,
    source_to_id_attribute: str = DEFAULT_SOURCE_ID_ATTRIBUTE,
    source_to_geometry_attribute: str = DEFAULT_SOURCE_GEOMETRY_ATTRIBUTE,
    target_layer_alias: Optional[str] = None,
    target_layer_parent_id: Optional[str] = None,
    transport_type: Optional[str] = None,
    id_attribute_name: str = DEFAULT_ID_ATTRIBUTE_NAME,
    id_from_attribute_name: str = DEFAULT_ID_FROM_ATTRIBUTE_NAME,
    id_to_attribute_name: str = DEFAULT_ID_TO_ATTRIBUTE_NAME,
    transport_type_attribute_name: str = DEFAULT_TRANSPORT_TYPE_ATTRIBUTE_NAME,
    weight_parameter_attribute_name: str = DEFAULT_WEIGHT_PARAMETER_ATTRIBUTE_NAME,
    distance_attribute_name: str = DEFAULT_DISTANCE_ATTRIBUTE_NAME,
    attribute_type_mapping: Optional[Dict[str, str]] = None,
    default_values: Optional[Dict[str, Any]] = None,
    enabled: bool = True,
    start_if_previous_error: bool = True,
    start_if_previous_not_finished: bool = True,
    order: Optional[int] = None,
    description: Optional[str] = None,
    wait_for_completion: bool = True,
    timeout: Optional[float] = 300,
    check_interval: float = 2.0,
    progress_callback: Optional[Callable[[TaskProgress], None]] = None,
    log: bool = False,
    defer: bool = False,
) -> "TaskExecutionResult | TaskStep":
    """Build an origin-destination matrix via ``netEngine:ODMatrix``.

    Args:
        client: Initialised EverGIS API client instance.
        target_layer: Target layer name to store the resulting matrix.
        source_from_layer_eql: EQL expression describing the FROM dataset.
        source_from_layer_name: Existing layer name for the FROM source (alternative to EQL).
        source_from_condition: Additional filter added to the FROM source definition.
        source_from_id_attribute: Identifier attribute in the FROM source (default: ``gid``).
        source_from_geometry_attribute: Geometry attribute in the FROM source (default: ``geometry``).
        source_to_layer_eql: EQL expression describing the TO dataset.
        source_to_layer_name: Existing layer name for the TO source (alternative to EQL).
        source_to_condition: Additional filter added to the TO source definition.
        source_to_id_attribute: Identifier attribute in the TO source (default: ``gid``).
        source_to_geometry_attribute: Geometry attribute in the TO source (default: ``geometry``).
        target_layer_alias: Alias of the target layer (optional).
        target_layer_parent_id: Parent source identifier for the target layer (optional).
        transport_type: Transport mode for the whole task - ``"car"`` or ``"pedestrian"``.
        id_attribute_name: Output attribute name for row identifier (default: ``gid``).
        id_from_attribute_name: Output attribute name for FROM id (default: ``from``).
        id_to_attribute_name: Output attribute name for TO id (default: ``to``).
        transport_type_attribute_name: Output attribute name for transport type
            (default: ``transport_type``).
        weight_parameter_attribute_name: Output attribute name for weight parameter
            (default: ``weight_parameter``).
        distance_attribute_name: Output attribute name for distance/metric value
            (default: ``distance``).
        attribute_type_mapping: Mapping ``{attribute_name: type}`` with explicit EverGIS
            types (``"Double"``, ``"Int64"``, ``"String"``, ``"Boolean"``, ``"DateTime"``)
            for attributes whose type differs from ``String``. Behaves like the import
            task mapping: if the target layer already exists its schema must contain
            these attributes, otherwise the task fails.
        default_values: Mapping ``{attribute_name: value}`` with values written into the
            target layer for each row. New attributes are created when the layer does
            not exist; otherwise they must already be present.
        enabled: Enable created task prototype (default: True).
        start_if_previous_error: Allow execution when previous run ended with error.
        start_if_previous_not_finished: Allow execution when previous run is still running.
        order: Subtask order inside the prototype.
        description: Prototype description shown in scheduler.
        wait_for_completion: Wait for task completion before returning (default: True).
        timeout: Timeout for waiting (seconds). ``None`` disables timeout.
        check_interval: Interval between status checks while waiting.
        progress_callback: Custom callback invoked with progress updates.
        log: Verbose output (JSON prototype, execution statuses).

    Returns:
        TaskExecutionResult describing the execution outcome.
    """
    if not target_layer:
        raise ValueError("Parameter 'target_layer' must be provided and not empty.")
    if not source_from_layer_eql and not source_from_layer_name:
        raise ValueError(
            "Either 'source_from_layer_eql' or 'source_from_layer_name' must be provided."
        )
    if not source_to_layer_eql and not source_to_layer_name:
        raise ValueError(
            "Either 'source_to_layer_eql' or 'source_to_layer_name' must be provided."
        )

    source_from_config = SourceEqlConfig(
        eql=source_from_layer_eql,
        layer_name=source_from_layer_name,
        condition=source_from_condition,
        id_attribute=source_from_id_attribute,
        geometry_attribute=source_from_geometry_attribute,
    )

    source_to_config = SourceEqlConfig(
        eql=source_to_layer_eql,
        layer_name=source_to_layer_name,
        condition=source_to_condition,
        id_attribute=source_to_id_attribute,
        geometry_attribute=source_to_geometry_attribute,
    )

    target_layer_config = LayerReferenceConfig(
        name=target_layer,
        alias=target_layer_alias,
        parent_id=target_layer_parent_id,
    )

    start_parameters = NetengineOdmatrixStartParameters(
        proccessingType="ODMatrix",
        source_from_layer=source_from_config,
        source_to_layer=source_to_config,
        target_layer=target_layer_config,
        transport_type=transport_type,
        id_attribute_name=id_attribute_name,
        id_from_attribute_name=id_from_attribute_name,
        id_to_attribute_name=id_to_attribute_name,
        transport_type_attribute_name=transport_type_attribute_name,
        weight_parameter_attribute_name=weight_parameter_attribute_name,
        distance_attribute_name=distance_attribute_name,
        attribute_type_mapping=attribute_type_mapping,
        default_values=default_values,
    )

    if defer:
        return TaskStep(
            task_type='netEngine',
            start_parameters=start_parameters.model_dump(by_alias=True, exclude_none=True),
            description=description,
            order=order,
        )

    prototype = create_task_prototype(
        "netEngine:ODMatrix",
        start_parameters=start_parameters.model_dump(by_alias=True, exclude_none=True),
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


__all__ = ["build_od_matrix"]
