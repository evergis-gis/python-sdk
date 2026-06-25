"""Simple example of getting a task status by ID.

This example shows:
1. How to get the current status of a task by its ID
2. How to track the progress of a running task
3. How to handle possible errors
"""

import time
from uuid import UUID
from evergis_tools import Client
from evergis_tools.tasks import TaskManager
from evergis_tools.tasks.models import TaskProgress


def get_single_status(manager: TaskManager, task_id: UUID) -> None:
    """Get task status once and print information.

    Args:
        manager: TaskManager instance
        task_id: Task ID to check
    """
    print(f"\n{'=' * 60}")
    print(f"Getting task status: {task_id}")
    print(f"{'=' * 60}")

    try:
        # Get the task status
        progress: TaskProgress = manager.get_task_status(task_id)

        # Print the main information
        print(f"Status: {progress.status.value}")
        print(f"Overall progress: {progress.overall_progress:.1f}%")

        # Information about the current subtask
        if progress.current_subtask:
            print(f"Current subtask: {progress.current_subtask}")
            print(f"Subtask progress: {progress.subtask_progress:.1f}%")

        # Information about the number of processed records
        if progress.processed_count is not None and progress.total_count is not None:
            print(f"Records processed: {progress.processed_count}/{progress.total_count}")

        # Current message
        if progress.message:
            print(f"Message: {progress.message}")

        # Running check
        if progress.is_running:
            print("• Task is running...")
        else:
            print("✓ Task finished")

        # Errors
        if progress.error_message:
            print(f"✗ Error: {progress.error_message}")

    except Exception as e:
        print(f"✗ Error while getting status: {e}")


def monitor_task(manager: TaskManager, task_id: UUID, check_interval: float = 2.0) -> None:
    """Monitor task until completion with simple polling.

    Args:
        manager: TaskManager instance
        task_id: Task ID to monitor
        check_interval: Seconds between status checks
    """
    print(f"\n{'=' * 60}")
    print(f"Monitoring task: {task_id}")
    print(f"Checking every {check_interval} seconds...")
    print(f"{'=' * 60}\n")

    try:
        while True:
            progress = manager.get_task_status(task_id)

            # Print the progress
            status_icon = "•" if progress.is_running else "✓"
            print(
                f"{status_icon} [{progress.status.value}] "
                f"Progress: {progress.overall_progress:.1f}% "
                f"| {progress.current_subtask or 'N/A'}"
            )

            # If the task finished or failed - exit
            if not progress.is_running:
                print(f"\n{'=' * 60}")
                if progress.error_message:
                    print(f"✗ Task finished with an error: {progress.error_message}")
                else:
                    print("✓ Task finished successfully!")
                print(f"{'=' * 60}\n")
                break

            # Wait before the next check
            time.sleep(check_interval)

    except KeyboardInterrupt:
        print("\n• Monitoring interrupted by the user")
    except Exception as e:
        print(f"\n✗ Error while monitoring: {e}")


def main() -> None:
    """Main example function."""
    # Create the client and task manager (host/token are read from env / .env)
    with Client() as client:
        manager = TaskManager(client)

        # IMPORTANT: Provide a real task ID to check.
        # You can get it when creating a task or from the task list.
        task_id_str = "00000000-0000-0000-0000-000000000000"  # Replace with a real ID
        task_id = UUID(task_id_str)

        # Example 1: single status check
        get_single_status(manager, task_id)

        # Example 2: monitor the task until completion (uncomment if needed)
        # monitor_task(manager, task_id, check_interval=2.0)


if __name__ == "__main__":
    main()
