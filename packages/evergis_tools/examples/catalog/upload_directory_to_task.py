"""Example demonstrating directory upload to TaskResource.

This example shows how to upload an entire directory to a TaskResource
using the special .task/ path format. The structure is preserved inside
the TaskResource.
"""

from evergis_tools import Client
from evergis_tools.catalog import upload_directory

# Set up EverGIS client with host URL and user token
client = Client()

# Get the username from the created session
username = client.account.get_user_info().username

# Source directory to upload
SOURCE_DIR = "project_samples/converters"

# TaskResource path format: "owner/path/to/task.task/internal/path"
# The .task extension indicates this is a TaskResource
parent_path = f"{username}/Projects/GIN ML real estate/scripts/test_project.task/src"

if __name__ == "__main__":
    # Upload to TaskResource with custom ignore patterns
    results = upload_directory(
        client=client,
        directory_path=SOURCE_DIR,
        parent_path=parent_path,
        owner=username,
        rewrite=True,
        ignore_patterns=[
            "__pycache__",
            "*.pyc",
            ".DS_Store",
            "*.log",
            "*.tmp",
        ],
        sync=True,
    )

