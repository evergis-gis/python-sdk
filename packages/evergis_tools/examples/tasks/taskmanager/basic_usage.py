"""Example of using TaskManager to work with EverGIS tasks."""

from uuid import UUID
from evergis_tools import Client
from evergis_tools.tasks import TaskManager, TaskFilter


def main() -> None:
    client = Client()
    manager = TaskManager(client)
    task_filter = TaskFilter(torder_by="createdAt")
    prototypes = manager.get_prototypes(task_filter)
    
    print (prototypes)
    
    if not prototypes:
        print("No prototypes found")
        return

    print("Available prototypes:")
    for proto in prototypes:
        prototype_id = getattr(proto, "id", UUID(int=0))
        created_at = getattr(proto, "createdAt", None)
        last_task_finish = getattr(proto, "lastTaskFinish", None)
        duration = (last_task_finish - created_at) if (last_task_finish and created_at) else 'N/A'
        status = getattr(proto, "lastTaskStatus", None)
        user = getattr(proto, "user", None)
        
        if user == "polyakov":
            manager.delete_prototype(prototype_id)
            print(f"Prototype {prototype_id} deleted")

        print(
            "-" * 80 + "\n",
            f"\033[1m{user}\033[0m"
            f"| {status} "
            f"| {created_at.strftime('%Y-%m-%d %H:%M:%S') if created_at else 'N/A'} "
            f"| Run time: {duration} "
            f"| {prototype_id} "
        )

        # for name, value in vars(proto).items():
        #     print(f"{name} = {value}")


        tasks = manager.get_tasks_for_prototype(prototype_id)
        
        if len(tasks) > 0:
            print("Current tasks:")
            for task in tasks:
                if task.id is None:
                    continue
                task_id = task.id
                progress = manager.get_task_status(task_id)
                
                print(
                    f"- {task_id}" 
                    f" - {progress.status.value}, "
                    f" - {progress.overall_progress:.1f}%"
                )
                subtasks = manager.get_task_subtasks(task_id)
                for subtask in subtasks:
                    subtask_finished = getattr(subtask, "ended", None).strftime("%Y-%m-%d %H:%M:%S") if getattr(subtask, "ended", None) else "N/A"
                    subtask_status = getattr(subtask, "status", None)
                    subtask_type = getattr(subtask, "type", None)
                    results = getattr(subtask, "results", None)
                    error_message = getattr(subtask, "errorMessage", None)
                    print (
                        f"  - {subtask_type} | {subtask_status} | Finished: {subtask_finished}"
                    )
                    if results and isinstance(results, str):
                        print (f"  - Results: \n"
                               f" {results[:100]}"
                               )
                    if error_message:
                        print (f"  - Error: {error_message}"
                               )

                    # for name, value in vars(subtask).items():
                    #     print(f"{name} = {value}")


if __name__ == "__main__":
    main()
