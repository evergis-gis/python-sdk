"""Task utilities for EverGIS."""

from typing import Callable, Optional

from evergis_api import Client
from evergis_api.schemas import TaskPrototypeDto

from .manager import TaskManager
from .models import TaskExecutionResult, TaskProgress, TaskWaitOptions

__all__ = [
    "create_progress_callback",
    "create_simple_progress_callback",
    "run_task",
]

# ANSI color codes
GREEN = "\033[92m"
RED = "\033[91m"
YELLOW = "\033[93m"
RESET = "\033[0m"


def _format_progress(progress: TaskProgress) -> str:
    """Format progress info: 'Status | processed/total (percent%)' or 'Status | processed'.

    Args:
        progress: TaskProgress with processed_count, total_count, status.

    Returns:
        Formatted string like 'Process | 1500/24447 (6%)' or 'Process | 1500' or 'Process'.
    """
    status = progress.status.name.capitalize()
    if progress.processed_count is not None and progress.total_count and progress.total_count > 0:
        pct = 100.0 * progress.processed_count / progress.total_count
        return f"{status} | {progress.processed_count}/{progress.total_count} ({pct:.0f}%)"
    elif progress.processed_count is not None:
        return f"{status} | {progress.processed_count}"
    else:
        return status


def _get_status_symbol(status_name: str) -> str:
    """Get colored symbol for status.

    Args:
        status_name: Status name like 'COMPLETED', 'ERROR', 'PROCESS'.

    Returns:
        Colored symbol: green checkmark, red cross, or yellow bullet.
    """
    if status_name == "COMPLETED":
        return f"{GREEN}\u2713{RESET}"
    elif status_name in ("ERROR", "FAILED", "INTERRUPTED", "TIMEOUT"):
        return f"{RED}\u2717{RESET}"
    else:
        return f"{YELLOW}\u2022{RESET}"


def create_progress_callback(check_interval: float = 2.0) -> Callable[[TaskProgress], None]:
    """Create a detailed progress callback with elapsed time.

    Args:
        check_interval: Progress check interval in seconds (default: 2.0).

    Returns:
        Progress callback function suitable for TaskWaitOptions.
    """
    poll_count = {"value": 0}

    def progress_callback(progress: TaskProgress) -> None:
        poll_count["value"] += 1
        elapsed = int(poll_count["value"] * check_interval)
        symbol = _get_status_symbol(progress.status.name)
        info = _format_progress(progress)
        print(f"{symbol} {info} | {elapsed}s")

    return progress_callback


def create_simple_progress_callback() -> Callable[[TaskProgress], None]:
    """Create a simple progress callback without elapsed time.

    Returns:
        Basic progress callback function.
    """

    def simple_progress_callback(progress: TaskProgress) -> None:
        symbol = _get_status_symbol(progress.status.name)
        info = _format_progress(progress)
        print(f"{symbol} {info}")

    return simple_progress_callback


def run_task(
    client: Client,
    prototype: TaskPrototypeDto,
    *,
    wait_for_completion: bool = True,
    timeout: Optional[float] = 300,
    check_interval: float = 2.0,
    progress_callback: Optional[Callable[[TaskProgress], None]] = None,
    raise_on_failure: bool = True,
    log: bool = False,
) -> TaskExecutionResult:
    """Create TaskManager and run task with standard wait options.

    Args:
        client: EverGIS API client.
        prototype: Task prototype to run.
        wait_for_completion: Wait for task completion (default: True).
        timeout: Wait timeout in seconds (None disables timeout).
        check_interval: Status check interval in seconds.
        progress_callback: Custom progress callback (if not provided, one will be created).
        raise_on_failure: Raise ``TaskFailedError`` if the task ends in a failed
            state (default: True). Pass False to get the failed result back instead.
        log: Detailed output - JSON prototype, progress with time (default: True).

    Returns:
        TaskExecutionResult with final status or initial status if not waiting.

    Raises:
        TaskFailedError: If the task fails and ``raise_on_failure`` is True.
    """
    manager = TaskManager(client)

    wait_options: Optional[TaskWaitOptions] = None
    if wait_for_completion:
        callback = progress_callback
        if callback is None:
            if log:
                callback = create_progress_callback(check_interval=check_interval)
            else:
                callback = create_simple_progress_callback()
        wait_options = TaskWaitOptions(
            timeout=timeout,
            check_interval=check_interval,
            progress_callback=callback,
            raise_on_failure=raise_on_failure,
        )
    elif progress_callback:
        wait_options = TaskWaitOptions(
            timeout=timeout,
            check_interval=check_interval,
            progress_callback=progress_callback,
            raise_on_failure=raise_on_failure,
        )

    return manager.create_and_run(
        task=prototype,
        wait_for_completion=wait_for_completion,
        wait_options=wait_options,
        log=log,
    )
