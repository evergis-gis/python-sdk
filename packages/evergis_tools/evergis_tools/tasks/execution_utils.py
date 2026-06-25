"""Helpers that convert raw subtask responses into execution results."""

from __future__ import annotations

from datetime import datetime
from typing import Dict, Optional, Sequence
from uuid import UUID

from evergis_api.schemas import RemoteTaskStatus, SubTasksDto

from .models import TaskExecutionResult
from .statuses import FAILED_STATUSES, RUNNING_STATUSES


def build_execution_result(
    task_id: UUID,
    subtasks: Sequence[SubTasksDto],
    *,
    prototype_id: Optional[UUID] = None,
) -> TaskExecutionResult:
    """Create :class:`TaskExecutionResult` using API subtask payloads."""
    if not subtasks:
        return TaskExecutionResult(
            task_id=task_id,
            prototype_id=prototype_id,
            status=RemoteTaskStatus.UNKNOWN,
        )

    overall_status = _resolve_overall_status(subtasks)
    started, ended = _collect_time_bounds(subtasks)
    duration = _compute_duration(started, ended)

    return TaskExecutionResult(
        task_id=task_id,
        prototype_id=prototype_id,
        status=overall_status,
        started=started,
        ended=ended,
        duration=duration,
        subtasks=list(subtasks),
        error_message=_collect_error_message(subtasks),
        results=_merge_results(subtasks),
    )


def _resolve_overall_status(subtasks: Sequence[SubTasksDto]) -> RemoteTaskStatus:
    status = RemoteTaskStatus.COMPLETED
    for subtask in subtasks:
        current = _safe_status(subtask.status)
        if current in FAILED_STATUSES:
            return current
        if current in RUNNING_STATUSES:
            status = current
        elif current not in {RemoteTaskStatus.COMPLETED}:
            status = current
    return status


def _collect_time_bounds(
    subtasks: Sequence[SubTasksDto],
) -> tuple[Optional[datetime], Optional[datetime]]:
    started: Optional[datetime] = None
    ended: Optional[datetime] = None
    for subtask in subtasks:
        if subtask.started and (started is None or subtask.started < started):
            started = subtask.started
        if subtask.ended and (ended is None or subtask.ended > ended):
            ended = subtask.ended
    return started, ended


def _compute_duration(started: Optional[datetime], ended: Optional[datetime]) -> Optional[float]:
    if started and ended:
        return (ended - started).total_seconds()
    return None


def _collect_error_message(subtasks: Sequence[SubTasksDto]) -> Optional[str]:
    messages = [
        subtask.errorMessage for subtask in subtasks if getattr(subtask, "errorMessage", None)
    ]
    if not messages:
        return None
    return "; ".join(messages)


def _merge_results(subtasks: Sequence[SubTasksDto]) -> Dict[str, object]:
    merged: Dict[str, object] = {}
    for subtask in subtasks:
        if subtask.results:
            merged.update(subtask.results)
    return merged


def _safe_status(status: Optional[RemoteTaskStatus]) -> RemoteTaskStatus:
    return status or RemoteTaskStatus.UNKNOWN


__all__ = [
    "build_execution_result",
]
