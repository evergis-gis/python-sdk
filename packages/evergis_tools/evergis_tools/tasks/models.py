"""Pydantic models for working with EverGIS tasks."""

from typing import Optional, List, Dict, Any, Callable, Iterable
from datetime import datetime
from uuid import UUID

from pydantic import BaseModel, Field, ConfigDict, field_validator

from evergis_api.schemas import RemoteTaskStatus, SubTasksDto

from .progress_utils import build_progress_snapshot


class TaskExecutionResult(BaseModel):
    """Result of a task execution."""

    task_id: UUID = Field(..., description="ID of the executed task")
    prototype_id: Optional[UUID] = Field(None, description="Task prototype ID")
    status: RemoteTaskStatus = Field(..., description="Final status")
    started: Optional[datetime] = Field(None, description="Start time")
    ended: Optional[datetime] = Field(None, description="End time")
    duration: Optional[float] = Field(None, description="Execution duration in seconds")
    subtasks: List[SubTasksDto] = Field(default_factory=list, description="Subtask results")
    error_message: Optional[str] = Field(None, description="Error message")
    results: Dict[str, Any] = Field(default_factory=dict, description="Execution results")

    @property
    def is_successful(self) -> bool:
        """Check whether the task finished successfully."""
        return self.status == RemoteTaskStatus.COMPLETED

    @property
    def is_failed(self) -> bool:
        """Check whether the task finished with an error."""
        return self.status in [
            RemoteTaskStatus.ERROR,
            RemoteTaskStatus.INTERRUPTED,
            RemoteTaskStatus.TIMEOUT,
        ]

    @property
    def is_running(self) -> bool:
        """Check whether the task is currently running."""
        return self.status in [
            RemoteTaskStatus.INIT,
            RemoteTaskStatus.PROCESS,
            RemoteTaskStatus.WAITING,
            RemoteTaskStatus.INQUEUE,
        ]


class TaskFailedError(RuntimeError):
    """Raised when an EverGIS task finishes in a failed state.

    Carries the full :class:`TaskExecutionResult` (``result``) so callers
    can inspect ``status`` / ``error_message`` / ``subtasks``. Raised by
    ``wait_for_completion`` when ``TaskWaitOptions.raise_on_failure`` is set
    (the default), so a server-side task failure surfaces as an exception
    instead of a result that silently looks like success.
    """

    def __init__(self, result: "TaskExecutionResult"):
        self.result = result
        message = result.error_message or (
            f"Task {result.task_id} finished with status {result.status.name}"
        )
        super().__init__(message)


class TaskProgress(BaseModel):
    """Task execution progress."""

    task_id: UUID = Field(..., description="Task ID")
    overall_progress: float = Field(0.0, description="Overall progress 0-100%")
    current_subtask: Optional[str] = Field(None, description="Current subtask")
    current_subtask_id: Optional[UUID] = Field(None, description="Current subtask ID")
    subtask_progress: float = Field(0.0, description="Current subtask progress 0-100%")
    status: RemoteTaskStatus = Field(..., description="Current status")
    message: Optional[str] = Field(None, description="Current status message")
    processed_count: Optional[int] = Field(None, description="Number of processed records")
    total_count: Optional[int] = Field(None, description="Total number of records")
    error_message: Optional[str] = Field(
        None, description="Error message of the last subtask"
    )

    @property
    def is_running(self) -> bool:
        """Check whether the task is currently running."""
        return self.status in [
            RemoteTaskStatus.INIT,
            RemoteTaskStatus.PROCESS,
            RemoteTaskStatus.WAITING,
            RemoteTaskStatus.INQUEUE,
        ]

    @classmethod
    def from_subtasks(cls, task_id: UUID, subtasks: List[SubTasksDto]) -> "TaskProgress":
        """Build progress from a list of subtasks."""
        snapshot = build_progress_snapshot(subtasks)
        return cls(
            task_id=task_id,
            overall_progress=snapshot.overall_progress,
            current_subtask=snapshot.current_subtask,
            current_subtask_id=snapshot.current_subtask_id,
            subtask_progress=snapshot.subtask_progress,
            status=snapshot.status,
            message=(
                snapshot.error_message if snapshot.status != RemoteTaskStatus.COMPLETED else None
            ),
            processed_count=snapshot.processed_count,
            total_count=snapshot.total_count,
            error_message=snapshot.error_message,
        )


class TaskWaitOptions(BaseModel):
    """Options for waiting on task completion."""

    timeout: Optional[float] = Field(None, description="Timeout in seconds")
    check_interval: float = Field(2.0, description="Status check interval in seconds")
    progress_callback: Optional[Callable[[TaskProgress], None]] = Field(
        None, description="Progress callback"
    )
    raise_on_failure: bool = Field(
        True,
        description="Raise TaskFailedError if the task finished with an error",
    )

    model_config = ConfigDict(arbitrary_types_allowed=True)


class TaskFilter(BaseModel):
    """Filter for searching tasks."""

    user: Optional[str] = Field(None, description="User")
    status: Optional[RemoteTaskStatus] = Field(None, description="Status")
    created_after: Optional[datetime] = Field(None, description="Created after")
    created_before: Optional[datetime] = Field(None, description="Created before")
    skip: int = Field(0, description="Records to skip")
    take: int = Field(50, description="Records to take")
    order_by: Optional[str] = Field(None, description="Sort order")
    desc: bool = Field(True, description="Descending")

    def to_api_kwargs(
        self,
        *,
        include_username: bool = True,
        allowed_fields: Optional[Iterable[str]] = None,
    ) -> Dict[str, Any]:
        """Convert the filter into a set of arguments for the REST API methods.

        Args:
            include_username: Whether to add the Username field (where supported).
            allowed_fields: Fields allowed for a specific endpoint. If provided,
                using a disallowed field raises ``ValueError``.
        """

        params: Dict[str, Any] = {
            "Skip": self.skip,
            "Take": self.take,
            "Desc": self.desc,
        }

        if self.order_by:
            params["OrderBy"] = self.order_by

        if include_username and self.user:
            params["Username"] = self.user
        if self.status:
            params["Status"] = self.status
        if self.created_after:
            params["CreatedAfter"] = self.created_after
        if self.created_before:
            params["CreatedBefore"] = self.created_before

        if allowed_fields is not None:
            allowed = set(allowed_fields)
            unsupported = {key for key in params if key not in allowed}
            if unsupported:
                fields = ", ".join(sorted(unsupported))
                raise ValueError(
                    f"TaskFilter fields {fields} are not supported for the selected method."
                )
            params = {key: value for key, value in params.items() if key in allowed}

        return params


class ScheduleOptions(BaseModel):
    """Task scheduling options."""

    schedule: Optional[str] = Field(None, description="Cron expression for the schedule")
    delay_date: Optional[datetime] = Field(None, description="Delayed start date")
    enabled: bool = Field(True, description="Whether the prototype is enabled")
    start_if_previous_error: bool = Field(False, description="Start on previous run error")
    start_if_previous_not_finished: bool = Field(
        False, description="Start if the previous run has not finished"
    )

    @field_validator("schedule")
    @classmethod
    def validate_schedule(cls, v):
        if v and len(v.split()) not in [5, 6]:
            raise ValueError("Schedule must be a valid cron expression")
        return v
