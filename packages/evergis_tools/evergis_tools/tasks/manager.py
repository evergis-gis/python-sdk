"""
High-level manager for orchestrating EverGIS tasks.
"""

import logging
from typing import Optional, List
from uuid import UUID
import time

from .execution_utils import build_execution_result
from .models import (
    TaskExecutionResult,
    TaskFailedError,
    TaskProgress,
    TaskWaitOptions,
    TaskFilter,
    ScheduleOptions,
)

from evergis_api import Client
from evergis_api.schemas import (
    ActiveWorkerDc,
    TaskConfigurationDc,
    TaskDto,
    TaskPrototypeDto,
    SubTasksDto,
    UpdateTaskPrototypeDto,
    WorkerStartMethodDto,
)

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"

logger = logging.getLogger(__name__)


class TaskManager:
    """
    High-level manager for orchestrating EverGIS tasks.

    Provides convenient methods for:
    - Creating and scheduling tasks
    - Starting and monitoring execution
    - Retrieving results and statistics
    """

    def __init__(self, client: Client):
        """
        Initialize the task manager.

        Args:
            client: EverGIS API client
        """
        if not client:
            raise ValueError("EverGIS API client is required")
        self.client = client

    def create_prototype(
        self, task: TaskPrototypeDto, schedule_options: Optional[ScheduleOptions] = None
    ) -> UUID:
        """
        Create a task prototype.

        Args:
            task: Task prototype for the API
            schedule_options: Scheduling options (schedule, delayed start)

        Returns:
            UUID: ID of the created prototype
        """
        # Apply scheduling options
        if schedule_options:
            if schedule_options.schedule:
                task.schedule = schedule_options.schedule
            if schedule_options.delay_date:
                task.delayDate = schedule_options.delay_date
            task.enabled = schedule_options.enabled
            task.startIfPreviousError = schedule_options.start_if_previous_error
            task.startIfPreviousNotFinished = schedule_options.start_if_previous_not_finished

        # Create the prototype via the API
        prototype_id = self.client.remotetaskmanager.create_task_prototype(body=task)
        return prototype_id

    def start_task(self, prototype_id: UUID) -> UUID:
        """
        Start a task from a prototype.

        Args:
            prototype_id: Task prototype ID

        Returns:
            UUID: ID of the started task
        """
        result = self.client.remotetaskmanager.start_task_1(prototype_id)
        if not result.success:
            raise RuntimeError(f"Failed to start task: {result}")
        return result.id

    def create_and_run(
        self,
        task: TaskPrototypeDto,
        wait_for_completion: bool = True,
        wait_options: Optional[TaskWaitOptions] = None,
        log: bool = False,
    ) -> TaskExecutionResult:
        """
        Create a prototype and immediately start the task.

        Args:
            task: Task prototype for the API
            wait_for_completion: Whether to wait for execution to finish
            wait_options: Wait options (timeout, callbacks)
            log: Verbose output (JSON prototype, task id)

        Returns:
            TaskExecutionResult: Execution result
        """
        if log:
            print(f"{YELLOW}•{RESET} Task prototype:")
            print(task.model_dump_json(indent=2, exclude_none=True))

        prototype_id, task_id = self._create_and_start(task)

        if log:
            print(
                f"{YELLOW}•{RESET} Task started",
                f"prototype_id={prototype_id}",
                f"task_id={task_id}",
            )

        if wait_for_completion:
            wait_args = wait_options or TaskWaitOptions()
            return self.wait_for_completion(
                task_id,
                wait_args,
                prototype_id=prototype_id,
                log=log,
            )

        subtasks = self.client.remotetaskmanager.get(task_id) or []
        return build_execution_result(
            task_id=task_id,
            subtasks=subtasks,
            prototype_id=prototype_id,
        )

    def _create_and_start(self, task: TaskPrototypeDto) -> tuple[UUID, UUID]:
        """Create a prototype and start the task, returning both identifiers."""
        prototype_id = self.create_prototype(task)
        task_id = self.start_task(prototype_id)
        return prototype_id, task_id

    def wait_for_completion(
        self,
        task_id: UUID,
        options: Optional[TaskWaitOptions] = None,
        *,
        prototype_id: Optional[UUID] = None,
        log: bool = False,
    ) -> TaskExecutionResult:
        """
        Wait for a task to finish, with optional progress tracking.

        Args:
            task_id: Task ID
            options: Wait options
            prototype_id: Prototype ID (if known); included in the execution result
            log: Verbose output

        Returns:
            TaskExecutionResult: Execution result
        """
        if not options:
            options = TaskWaitOptions()

        start_time = time.time()

        while True:
            # Fetch the current state
            subtasks = self.client.remotetaskmanager.get(task_id)
            if not subtasks:
                if log:
                    print(
                        f"{RED}✗{RESET} Subtasks not found",
                        f"prototype_id={prototype_id}",
                        f"task_id={task_id}",
                    )
                raise RuntimeError(f"Task {task_id} not found")

            # Build the progress snapshot
            progress = TaskProgress.from_subtasks(task_id, subtasks)

            # Invoke the callback if present
            # a broken callback must not kill the polling loop
            if options.progress_callback:
                try:
                    options.progress_callback(progress)
                except Exception:
                    logger.warning("Error in progress_callback", exc_info=True)

            # Check for completion
            if not progress.is_running:
                result = build_execution_result(
                    task_id=task_id,
                    subtasks=subtasks,
                    prototype_id=prototype_id,
                )
                # Print the error message if present
                if result.error_message:
                    print(f"{RED}✗{RESET} Error: {result.error_message}")
                # A failed server task must not look like success: raise so the
                # caller cannot accidentally proceed on a result that never
                # actually completed. Opt out via raise_on_failure=False.
                if options.raise_on_failure and result.is_failed:
                    raise TaskFailedError(result)
                return result

            # Check the timeout
            if options.timeout and (time.time() - start_time) > options.timeout:
                raise TimeoutError(f"Task {task_id} execution timeout")

            # Wait before the next check
            time.sleep(options.check_interval)

    def get_task_status(self, task_id: UUID) -> TaskProgress:
        """
        Get the current status and progress of a task.

        Args:
            task_id: Task ID

        Returns:
            TaskProgress: Execution progress
        """
        subtasks = self.client.remotetaskmanager.get(task_id) or []
        return TaskProgress.from_subtasks(task_id, subtasks)

    def stop_task(self, task_id: UUID) -> None:
        """Stop a running task.

        Args:
            task_id: Task ID.

        Raises:
            ApiClientError: If the server rejects the stop request.
        """
        self.client.remotetaskmanager.stop(task_id)

    def get_prototypes(self, task_filter: Optional[TaskFilter] = None) -> List[TaskPrototypeDto]:
        """
        Get the list of task prototypes.

        Args:
            task_filter: Search filter

        Returns:
            List[TaskPrototypeDto]: List of prototypes
        """
        filter_obj = task_filter or TaskFilter()

        api_kwargs = filter_obj.to_api_kwargs(
            include_username=True,
            allowed_fields={"Username", "Skip", "Take", "OrderBy", "Desc"},
        )

        result = self.client.remotetaskmanager.get_task_prototypes(**api_kwargs)

        return list(result.results or [])

    def get_tasks_for_prototype(
        self,
        prototype_id: UUID,
        task_filter: Optional[TaskFilter] = None,
    ) -> List[TaskDto]:
        """
        Get the list of tasks for a prototype.

        Args:
            prototype_id: Prototype ID
            task_filter: Search filter

        Returns:
            List[TaskDto]: List of tasks
        """
        filter_obj = task_filter or TaskFilter()

        api_kwargs = filter_obj.to_api_kwargs(
            include_username=False,
            allowed_fields={"Skip", "Take", "OrderBy", "Desc"},
        )

        result = self.client.remotetaskmanager.get_tasks_for_prototype(
            id=prototype_id,
            **api_kwargs,
        )

        return list(result.results or [])

    def update_prototype_schedule(
        self, prototype_id: UUID, schedule_options: ScheduleOptions
    ) -> None:
        """Update scheduling settings of a task prototype.

        Args:
            prototype_id: Prototype ID.
            schedule_options: New scheduling settings.

        Raises:
            ApiClientError: If the server rejects the update.
        """
        update_dto = UpdateTaskPrototypeDto(
            schedule=schedule_options.schedule,
            delayDate=schedule_options.delay_date,
            enabled=schedule_options.enabled,
            startIfPreviousError=schedule_options.start_if_previous_error,
            startIfPreviousNotFinished=schedule_options.start_if_previous_not_finished,
        )
        self.client.remotetaskmanager.update_task_prototype(id=prototype_id, body=update_dto)

    def delete_prototype(self, prototype_id: UUID) -> None:
        """Delete a task prototype.

        Raises:
            ApiClientError: If the server rejects the deletion.
        """
        self.client.remotetaskmanager.delete(prototype_id)

    def set_prototype_enabled(self, prototype_id: UUID, enabled: bool) -> None:
        """Enable or disable a task prototype.

        Raises:
            ApiClientError: If the server rejects the change.
        """
        self.client.remotetaskmanager.set_enable(prototype_id, enabled)

    def start_task_with_id(self, prototype_id: UUID, task_id: UUID) -> UUID:
        """Start a task with a predefined identifier."""
        result = self.client.remotetaskmanager.start_task(prototype_id, task_id)
        if not getattr(result, "success", True):
            message = getattr(result, "message", "")
            raise RuntimeError(f"Failed to start task {task_id}: {message}")
        return getattr(result, "id", task_id)

    def get_task_resource(
        self, resource_id: str, update_default: Optional[bool] = None
    ) -> TaskConfigurationDc:
        """Return the resource description for a task."""
        return self.client.remotetaskmanager.get_task_resource(
            resource_id,
            updateDefault=update_default,
        )

    def get_task_subtasks(self, task_id: UUID) -> List[SubTasksDto]:
        """Return the list of subtasks for the given task."""
        return self.client.remotetaskmanager.get(task_id)

    def get_active_workers(self) -> List[ActiveWorkerDc]:
        """Return the list of active workers."""
        return self.client.remotetaskmanager.get_1()

    def get_worker(self, worker_type: str) -> List[ActiveWorkerDc]:
        """Return information about a worker of the given type."""
        return self.client.remotetaskmanager.get_worker(worker_type)

    def run_worker_method(self, payload: WorkerStartMethodDto) -> bool:
        """Run a worker method."""
        return self.client.remotetaskmanager.post(body=payload)
