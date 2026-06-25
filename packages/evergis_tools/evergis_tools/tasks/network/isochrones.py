"""Helpers for EverGIS availability area (isochrones) tasks."""

from __future__ import annotations

from typing import Callable, Optional, Union

from evergis_api import Client

from ..models import TaskExecutionResult, TaskProgress
from ..pipeline import TaskStep
from ..utils import run_task
from ..worker_models import (
    LayerReferenceConfig,
    NetengineAvailabilityareaStartParameters,
    ProvidernameType,
    SourceEqlConfig,
    create_task_prototype,
)

DEFAULT_SOURCE_ID_ATTRIBUTE = "gid"
DEFAULT_SOURCE_GEOMETRY_ATTRIBUTE = "geometry"
DEFAULT_PROVIDER = ProvidernameType.SPROUTE_ISOCHRONE_PEDESTRIAN

ProviderNameLike = Union[ProvidernameType, str]


def build_isochrones(
    client: Client,
    *,
    source_layer_eql: Optional[str] = None,
    source_layer_name: Optional[str] = None,
    source_condition: Optional[str] = None,
    source_id_attribute: str = DEFAULT_SOURCE_ID_ATTRIBUTE,
    source_geometry_attribute: str = DEFAULT_SOURCE_GEOMETRY_ATTRIBUTE,
    provider_name: ProviderNameLike = DEFAULT_PROVIDER,
    duration_expression: Optional[str] = None,
    id_attribute_name: Optional[str] = None,
    geometry_attribute_name: Optional[str] = None,
    duration_attribute_name: Optional[str] = None,
    base_object_id_attribute_name: Optional[str] = None,
    route_center_x_attribute_name: Optional[str] = None,
    route_center_y_attribute_name: Optional[str] = None,
    target_layer: Optional[str] = None,
    target_layer_alias: Optional[str] = None,
    target_layer_parent_id: Optional[str] = None,
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
    """Builds an availability-area (isochrone) layer via ``netEngine:availabilityArea``.

    Args:
        client: Initialised EverGIS API client instance.
        source_layer_eql: EQL expression describing the source dataset.
        source_layer_name: Existing layer name to use when EQL is not provided.
        source_condition: Additional filter added to the source definition.
        source_id_attribute: Identifier attribute in the source (default: ``gid``).
        source_geometry_attribute: Geometry attribute in the source (default: ``geometry``).
        provider_name: NetEngine provider. Accepts ``ProvidernameType`` or its string value.
        duration_expression: Expression defining reach time / distance (provider specific).
        id_attribute_name: Output attribute name for feature identifier.
        geometry_attribute_name: Output attribute name for geometry.
        duration_attribute_name: Output attribute name for duration value.
        base_object_id_attribute_name: Output attribute name for base object id.
        route_center_x_attribute_name: Output attribute name for centroid X.
        route_center_y_attribute_name: Output attribute name for centroid Y.
        target_layer: Target layer name to store results (optional).
        target_layer_alias: Alias of the target layer (optional).
        target_layer_parent_id: Parent source identifier for the target layer (optional).
        enabled: Enable created task prototype (default: True).
        start_if_previous_error: Allow execution when previous run ended with error.
        start_if_previous_not_finished: Allow execution when previous run is still running.
        order: Subtask order inside the prototype.
        wait_for_completion: Wait for task completion before returning (default: True).
        timeout: Timeout for waiting (seconds). ``None`` disables timeout.
        check_interval: Interval between status checks while waiting.
        progress_callback: Custom callback invoked with progress updates.
        log: Verbose output (JSON prototype, execution statuses).

    Returns:
        TaskExecutionResult describing the execution outcome.
    """
    if not source_layer_eql and not source_layer_name:
        raise ValueError("Either 'source_layer_eql' or 'source_layer_name' must be provided.")

    provider_enum = (
        provider_name
        if isinstance(provider_name, ProvidernameType)
        else ProvidernameType(provider_name)
    )

    source_layer_config = SourceEqlConfig(
        eql=source_layer_eql,
        layer_name=source_layer_name,
        condition=source_condition,
        id_attribute=source_id_attribute,
        geometry_attribute=source_geometry_attribute,
    )

    target_layer_config = (
        LayerReferenceConfig(
            name=target_layer,
            alias=target_layer_alias,
            parent_id=target_layer_parent_id,
        )
        if target_layer
        else None
    )

    start_parameters = NetengineAvailabilityareaStartParameters(
        proccessingType="availabilityArea",
        provider_name=provider_enum,
        source_layer=source_layer_config,
        target_layer=target_layer_config,
        duration_expression=duration_expression,
        id_attribute_name=id_attribute_name,
        geometry_attribute_name=geometry_attribute_name,
        duration_attribute_name=duration_attribute_name,
        base_object_id_attribute_name=base_object_id_attribute_name,
        route_center_x_attribute_name=route_center_x_attribute_name,
        route_center_y_attribute_name=route_center_y_attribute_name,
    )

    if defer:
        return TaskStep(
            task_type='netEngine',
            start_parameters=start_parameters.model_dump(by_alias=True, exclude_none=True),
            description=description,
            order=order,
        )

    prototype = create_task_prototype(
        "netEngine:availabilityArea",
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


__all__ = ["build_isochrones"]
