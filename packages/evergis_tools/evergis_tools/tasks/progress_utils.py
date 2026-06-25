"""Utility helpers that convert raw subtask responses into progress snapshots."""

from __future__ import annotations

from dataclasses import dataclass
from typing import Dict, Optional, Sequence
from uuid import UUID

from evergis_api.schemas import RemoteTaskStatus, SubTasksDto

from .statuses import FAILED_STATUSES, RUNNING_STATUSES


@dataclass(frozen=True)
class ProgressSnapshot:
    """A lightweight container with pre-computed progress values."""

    status: RemoteTaskStatus
    overall_progress: float
    current_subtask: Optional[str]
    current_subtask_id: Optional[UUID]
    subtask_progress: float
    processed_count: Optional[int]
    total_count: Optional[int]
    error_message: Optional[str]


def build_progress_snapshot(subtasks: Sequence[SubTasksDto]) -> ProgressSnapshot:
    """Compute a :class:`ProgressSnapshot` from raw subtasks."""
    if not subtasks:
        return ProgressSnapshot(
            status=RemoteTaskStatus.UNKNOWN,
            overall_progress=0.0,
            current_subtask=None,
            current_subtask_id=None,
            subtask_progress=0.0,
            processed_count=None,
            total_count=None,
            error_message=None,
        )

    total_subtasks = len(subtasks)
    completed_subtasks = sum(
        1 for subtask in subtasks if _resolve_status(subtask.status) == RemoteTaskStatus.COMPLETED
    )
    active_subtask = _pick_active_subtask(subtasks)

    if active_subtask is not None:
        metrics = _collect_metrics(active_subtask)
        overall_progress = _combine_progress(
            total_subtasks=total_subtasks,
            completed_subtasks=completed_subtasks,
            current_progress=metrics.progress,
        )
        return ProgressSnapshot(
            status=metrics.status,
            overall_progress=overall_progress,
            current_subtask=active_subtask.type,
            current_subtask_id=getattr(active_subtask, "id", None),
            subtask_progress=metrics.progress,
            processed_count=metrics.processed_count,
            total_count=metrics.total_count,
            error_message=metrics.error_message,
        )

    # All subtasks are either completed or not started yet; fallback to the last one for context.
    last_subtask = subtasks[-1]
    last_metrics = _collect_metrics(last_subtask)
    overall_progress = _combine_progress(
        total_subtasks=total_subtasks,
        completed_subtasks=completed_subtasks,
        current_progress=0.0,
    )

    return ProgressSnapshot(
        status=last_metrics.status,
        overall_progress=overall_progress,
        current_subtask=last_subtask.type,
        current_subtask_id=getattr(last_subtask, "id", None),
        subtask_progress=last_metrics.progress,
        processed_count=last_metrics.processed_count,
        total_count=last_metrics.total_count,
        error_message=last_metrics.error_message,
    )


@dataclass(frozen=True)
class _SubtaskMetrics:
    status: RemoteTaskStatus
    progress: float
    processed_count: Optional[int]
    total_count: Optional[int]
    error_message: Optional[str]


def _collect_metrics(subtask: SubTasksDto) -> _SubtaskMetrics:
    status = _resolve_status(subtask.status)
    results = subtask.results or {}

    progress_from_results = _progress_from_results(results)
    processed_from_results = _to_int(results.get("Processed"))
    total_from_results = _to_int(results.get("Count"))

    # Try results["Processed"] first, then fallback to subtask.process
    processed_count = (
        processed_from_results if processed_from_results and processed_from_results >= 0 else None
    )
    if processed_count is None and subtask.process and subtask.process >= 0:
        processed_count = subtask.process

    # Try results["Count"] first, then fallback to subtask.max
    total_count = total_from_results if total_from_results and total_from_results > 0 else None
    if total_count is None and subtask.max and subtask.max > 0:
        total_count = subtask.max

    if progress_from_results is not None:
        subtask_progress = progress_from_results
    elif total_count and processed_from_results is not None and total_count > 0:
        subtask_progress = _clamp(100.0 * processed_from_results / total_count)
    elif subtask.max and subtask.max > 0:
        numerator = subtask.process or 0
        subtask_progress = _clamp(100.0 * numerator / subtask.max)
    else:
        subtask_progress = 0.0

    error_message = getattr(subtask, "errorMessage", None)

    return _SubtaskMetrics(
        status=status,
        progress=subtask_progress,
        processed_count=processed_count,
        total_count=total_count,
        error_message=error_message,
    )


def _pick_active_subtask(subtasks: Sequence[SubTasksDto]) -> Optional[SubTasksDto]:
    for subtask in subtasks:
        status = _resolve_status(subtask.status)
        if status in RUNNING_STATUSES or status in FAILED_STATUSES:
            return subtask
    return None


def _combine_progress(
    *, total_subtasks: int, completed_subtasks: int, current_progress: float
) -> float:
    if total_subtasks <= 0:
        return 0.0
    base_progress = (completed_subtasks / total_subtasks) * 100.0
    if current_progress <= 0.0:
        return _clamp(base_progress)
    per_subtask_share = 100.0 / total_subtasks
    combined = base_progress + per_subtask_share * (current_progress / 100.0)
    return _clamp(combined)


def _progress_from_results(results: Dict[str, object]) -> Optional[float]:
    raw_value = _to_float(results.get("Progress"))
    if raw_value is None:
        return None
    if raw_value <= 1.0:
        raw_value *= 100.0
    return _clamp(raw_value)


def _resolve_status(status: Optional[RemoteTaskStatus]) -> RemoteTaskStatus:
    return status or RemoteTaskStatus.UNKNOWN


def _clamp(value: float) -> float:
    if value < 0.0:
        return 0.0
    if value > 100.0:
        return 100.0
    return value


def _to_float(value: object) -> Optional[float]:
    if isinstance(value, (int, float)):
        return float(value)
    if isinstance(value, str):
        try:
            return float(value)
        except ValueError:
            return None
    return None


def _to_int(value: object) -> Optional[int]:
    number = _to_float(value)
    if number is None:
        return None
    return int(number)


__all__ = [
    "ProgressSnapshot",
    "build_progress_snapshot",
]
