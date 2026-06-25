"""Common status helpers for EverGIS task utilities."""

from __future__ import annotations

from evergis_api.schemas import RemoteTaskStatus

RUNNING_STATUSES = {
    RemoteTaskStatus.INIT,
    RemoteTaskStatus.PROCESS,
    RemoteTaskStatus.WAITING,
    RemoteTaskStatus.INQUEUE,
}
"""Statuses that indicate an active task or subtask execution."""

FAILED_STATUSES = {
    RemoteTaskStatus.ERROR,
    RemoteTaskStatus.INTERRUPTED,
    RemoteTaskStatus.TIMEOUT,
}
"""Statuses that indicate a failed or stopped task/subtask."""

TERMINAL_STATUSES = FAILED_STATUSES | {RemoteTaskStatus.COMPLETED, RemoteTaskStatus.UNKNOWN}
"""Statuses after which the server will not transition the task automatically."""

__all__ = [
    "FAILED_STATUSES",
    "RUNNING_STATUSES",
    "TERMINAL_STATUSES",
]
