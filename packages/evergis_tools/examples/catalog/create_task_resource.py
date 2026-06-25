"""Example demonstrating TaskResource creation in EverGIS catalog.

This example shows how to create an empty TaskResource (PythonTask).
If the parent folder doesn't exist, it will be created automatically.
"""


from evergis_tools import Client
from evergis_tools.catalog import create_task_resource

# Set up EverGIS client with host URL and user token
client = Client()

# Get the username from the created session
username = client.account.get_user_info().username

# TaskResource name (will have .task extension in catalog)
TASK_NAME = "my_processing_task"

# Parent folder path (will be created if doesn't exist)
PARENT_PATH = f"{username}/EverGIS Resources/python/tasks"

if __name__ == "__main__":
    print(f"Creating TaskResource: {TASK_NAME}")
    print(f"Parent path: {PARENT_PATH}")
    print(f"Owner: {username}\n")

    # Create empty TaskResource (auto-creates parent folders if needed)
    task_id = create_task_resource(
        client=client,
        name=TASK_NAME,
        parent_path=PARENT_PATH,
        description="Example task resource",
        tags=["example", "test"],
    )

    print("TaskResource created successfully!")
    print(f"Task ID: {task_id}")
    print(f"Full path: {PARENT_PATH}/{TASK_NAME}.task")
