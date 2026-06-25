"""Task pipeline: bundle multiple subtasks into one EverGIS prototype.

A single ``TaskPrototypeDto`` can carry several ``SubTaskSettingsDto``
items - the server runs them in order. The existing high-level
wrappers (``import_gpkg_to_layer``, ``export_layer_to_gpkg``,
``buffer_layer``, ...) each build a prototype with **one** subtask and
fire it immediately. That's fine for one-shot calls but doesn't let
users compose a multi-step server-side flow without making N round
trips and N independent prototypes.

This module adds two thin primitives on top of the existing machinery:

* :class:`TaskStep` - a frozen value object that captures everything
  needed to enqueue one subtask (``task_type``, dumped
  ``start_parameters``, optional ``description`` / ``order``).
* :class:`TaskPipeline` - a fluent builder that collects ``TaskStep``\
  s and submits them as a single prototype via
  :func:`create_task_prototype_multi`.

The existing wrappers gain an optional ``defer: bool = False``
parameter:

* ``defer=False`` (default) - **unchanged** behaviour: build a
  one-subtask prototype and run it.
* ``defer=True`` - return a :class:`TaskStep` instead, ready to drop
  into a pipeline.

The single-subtask helper :func:`create_task_prototype` in
``worker_models.models`` is untouched (generated code, regen-friendly);
we sit alongside it with :func:`create_task_prototype_multi`.

Example::

    from evergis_tools.tasks import TaskPipeline
    from evergis_tools.tasks.import_tools import import_gpkg_to_layer
    from evergis_tools.tasks.export_tools import export_layer_to_gpkg

    pipeline = TaskPipeline(description="import → export round-trip")
    pipeline.add(import_gpkg_to_layer(client, ..., defer=True))
    pipeline.add(export_layer_to_gpkg(client, ..., defer=True))
    result = pipeline.run(client, wait_for_completion=True)
"""

from __future__ import annotations

from dataclasses import dataclass
from datetime import datetime
from typing import Any, Callable, Optional, Sequence

from evergis_api.schemas import SubTaskSettingsDto, TaskPrototypeDto

from .models import TaskExecutionResult, TaskProgress
from .utils import run_task


# ---------------------------------------------------------------------------
# TaskStep - frozen value object
# ---------------------------------------------------------------------------

@dataclass(frozen=True)
class TaskStep:
    """One subtask, ready to be enqueued.

    ``start_parameters`` is the **dumped** dict (``by_alias=True,
    exclude_none=True``) - matching what
    :func:`create_task_prototype` already expects. The dataclass is
    frozen so a step can be safely passed around / reused.

    Attributes:
        task_type: Server-side task type. ``"importExport"``,
            ``"geoprocessing"``, ``"netengine"``, ... Subtype after
            ``":"`` (e.g. ``"importExport:importExport"``) is accepted
            for compatibility with the existing
            :func:`create_task_prototype` signature, but the server
            uses only the part before ``":"``.
        start_parameters: Already serialised startParameters payload
            (dict, not a Pydantic object).
        description: Optional subtask description (shows up in the
            scheduler / logs).
        order: Explicit execution order **or** ``None``.
            *  ``None`` (default) - server runs subtasks in **parallel**.
            *  Integer - server schedules them strictly by ``order``
               ascending (sequential).
            Mixing the two in one prototype is allowed: subtasks with
            an explicit order run in that order, ones without run
            concurrently with each other.
    """

    task_type: str
    start_parameters: dict[str, Any]
    description: Optional[str] = None
    order: Optional[int] = None


# ---------------------------------------------------------------------------
# Builder for a multi-subtask prototype
# ---------------------------------------------------------------------------

def create_task_prototype_multi(
    subtasks: Sequence[TaskStep],
    *,
    delay_date: Optional[datetime] = None,
    enabled: Optional[bool] = None,
    schedule: Optional[str] = None,
    start_if_previous_error: Optional[bool] = None,
    start_if_previous_not_finished: Optional[bool] = None,
    description: Optional[str] = None,
) -> TaskPrototypeDto:
    """Build a ``TaskPrototypeDto`` with several subtasks.

    Mirrors :func:`evergis_tools.tasks.worker_models.create_task_prototype`
    for the single-subtask case, but takes a sequence of
    :class:`TaskStep`\\ s. ``order`` is passed through as-is:
    ``None`` means parallel execution server-side; integer means
    sequential by that key.

    Args:
        subtasks: Steps to wrap. At least one required.
        delay_date / enabled / schedule / start_if_previous_error /
            start_if_previous_not_finished / description: Prototype-
            level scheduling knobs (same semantics as the single-
            subtask helper).

    Returns:
        A ``TaskPrototypeDto`` ready for the scheduler.
    """
    if not subtasks:
        raise ValueError("create_task_prototype_multi requires at least one subtask")

    sub_task_settings: list[SubTaskSettingsDto] = []
    for step in subtasks:
        main_type = step.task_type.split(":", 1)[0]
        sub_task_settings.append(
            SubTaskSettingsDto(
                order=step.order,                # None → server parallelises
                type=main_type,
                description=step.description,
                startParameters=step.start_parameters,
            )
        )

    return TaskPrototypeDto(
        delayDate=delay_date,
        enabled=enabled,
        schedule=schedule,
        startIfPreviousError=start_if_previous_error,
        startIfPreviousNotFinished=start_if_previous_not_finished,
        description=description,
        subTaskSettings=sub_task_settings,
    )


# ---------------------------------------------------------------------------
# Fluent pipeline builder
# ---------------------------------------------------------------------------

class TaskPipeline:
    """Collect :class:`TaskStep`\\ s and submit them as one prototype.

    Steps execute server-side **in order**. By default the pipeline
    stops if any subtask errors out (``start_if_previous_error=False``);
    pass ``start_if_previous_error=True`` to keep going regardless.

    Example::

        pipeline = TaskPipeline(description="Reindex from gpkg")
        pipeline.add(import_gpkg_to_layer(client, ..., defer=True))
        pipeline.add(buffer_layer(client, ..., defer=True))
        result = pipeline.run(client, wait_for_completion=True)

    For ad-hoc use without a wrapper::

        pipeline.add_subtask(
            "geoprocessing",
            start_parameters=GeoprocessingUnionStartParameters(...).model_dump(
                by_alias=True, exclude_none=True
            ),
            description="Union",
        )
    """

    def __init__(
        self,
        *,
        description: Optional[str] = None,
        enabled: bool = True,
        start_if_previous_error: bool = False,
        start_if_previous_not_finished: bool = False,
        schedule: Optional[str] = None,
        delay_date: Optional[datetime] = None,
    ) -> None:
        self.description = description
        self.enabled = enabled
        self.start_if_previous_error = start_if_previous_error
        self.start_if_previous_not_finished = start_if_previous_not_finished
        self.schedule = schedule
        self.delay_date = delay_date
        self._steps: list[TaskStep] = []

    # ---- assembly ----

    def add(self, step: TaskStep) -> "TaskPipeline":
        """Append a :class:`TaskStep`. Chainable."""
        if not isinstance(step, TaskStep):
            raise TypeError(
                f"TaskPipeline.add expects TaskStep (got {type(step).__name__}). "
                "Use add_subtask() for raw params or defer=True on a wrapper."
            )
        self._steps.append(step)
        return self

    def add_subtask(
        self,
        task_type: str,
        start_parameters: dict[str, Any],
        *,
        description: Optional[str] = None,
        order: Optional[int] = None,
    ) -> "TaskPipeline":
        """Convenience: build a :class:`TaskStep` inline and append it."""
        return self.add(
            TaskStep(
                task_type=task_type,
                start_parameters=start_parameters,
                description=description,
                order=order,
            )
        )

    @property
    def steps(self) -> tuple[TaskStep, ...]:
        """Read-only view of the steps collected so far."""
        return tuple(self._steps)

    # ---- submission ----

    def build(self) -> TaskPrototypeDto:
        """Materialise a ``TaskPrototypeDto`` without submitting it."""
        return create_task_prototype_multi(
            self._steps,
            delay_date=self.delay_date,
            enabled=self.enabled,
            schedule=self.schedule,
            start_if_previous_error=self.start_if_previous_error,
            start_if_previous_not_finished=self.start_if_previous_not_finished,
            description=self.description,
        )

    def run(
        self,
        client,
        *,
        wait_for_completion: bool = True,
        timeout: Optional[float] = 300,
        check_interval: float = 2.0,
        progress_callback: Optional[Callable[[TaskProgress], None]] = None,
        log: bool = False,
    ) -> TaskExecutionResult:
        """Build + run the prototype via :func:`run_task`.

        Identical semantics to the single-task helper - one
        ``progress_callback`` covers the whole pipeline (it already
        gets per-subtask progress from the scheduler).
        """
        prototype = self.build()
        return run_task(
            client=client,
            prototype=prototype,
            wait_for_completion=wait_for_completion,
            timeout=timeout,
            check_interval=check_interval,
            progress_callback=progress_callback,
            log=log,
        )


__all__ = ["TaskStep", "TaskPipeline", "create_task_prototype_multi"]
