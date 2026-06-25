"""TaskResource operations for EverGIS catalog.

TaskResources use special path format: taskId/internal/path
This module provides utilities for working with TaskResource internal structure.
"""

from __future__ import annotations

from pathlib import Path
from typing import List, Optional, Union

from evergis_api import Client
from evergis_api.schemas import (
    CatalogResourceDc,
    CatalogResourceType,
    ListResourcesDc,
    TaskResourceCreateDto,
    TaskResourceSubType,
)

from .folders import create_folder, get_or_create_folder_by_path
from .resources import resolve_parent_id


def create_task_resource(
    client: Client,
    name: str,
    parent_id: Optional[str] = None,
    *,
    parent_path: Optional[str] = None,
    system_name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    sub_type: TaskResourceSubType = TaskResourceSubType.PYTHONTASK,
) -> str:
    """Create a new empty TaskResource in the catalog.

    Args:
        client: EverGIS API client
        name: Name of the TaskResource (will have .task extension)
        parent_id: ID of the parent folder/resource. Mutually exclusive with parent_path.
        parent_path: Catalog path to parent folder (e.g., "john_doe:Projects/Tasks").
            If the path doesn't exist, all missing folders will be created automatically.
            Mutually exclusive with parent_id.
        description: Optional description for the TaskResource
        tags: Optional list of tags for the TaskResource
        sub_type: Task type (PythonTask or SpTask). Defaults to PythonTask.

    Returns:
        TaskResource UUID (resourceId)

    Raises:
        ValueError: If both parent_id and parent_path are provided, or neither is provided.

    Examples:
        >>> # Create TaskResource by parent_id
        >>> task_id = create_task_resource(
        ...     client,
        ...     name="my_task",
        ...     parent_id="6c02301ae0b94cf8a6f595b20890b1b7",
        ...     description="Task for data processing",
        ...     tags=["data", "processing"],
        ... )

        >>> # Create TaskResource by catalog path (auto-creates folders if needed)
        >>> task_id = create_task_resource(
        ...     client,
        ...     name="my_task",
        ...     parent_path="john_doe:Projects/Tasks",
        ...     description="Task for data processing",
        ... )
    """
    # Resolve parent folder ID
    resolved_parent_id = resolve_parent_id(client, parent_id, parent_path)

    # Build system_name. By default username.task_name; caller may
    # override with a fully-qualified name so different prototypes
    # don't collide in the catalog-wide systemName namespace.
    if system_name is None:
        username = client.account.get_user_info().username
        system_name = f"{username}.{name}"

    # Create TaskResource
    task_dto = TaskResourceCreateDto(
        name=name,
        systemName=system_name,
        subType=sub_type,
        parentId=resolved_parent_id,
        description=description,
        tags=tags or [],
    )

    return client.remotetaskmanager.create_task_resource(task_dto)


def is_task_resource_path(path: str) -> bool:
    """Detect if path is in TaskResource format.

    TaskResource paths can be:
    - Mixed: "john_doe:Projects/test.task/src/utils" (catalog path + .task/ + internal)
    - Direct: "6c02301ae0b94cf8a6f595b20890b1b7/src" (UUID/internal)

    Args:
        path: Path string to check

    Returns:
        True if path contains TaskResource pattern

    Examples:
        >>> is_task_resource_path("john_doe:Projects/test.task/src")
        True
        >>> is_task_resource_path("6c02301ae0b94cf8a6f595b20890b1b7/src/utils")
        True
        >>> is_task_resource_path("john_doe:Projects/Data")
        False
    """
    if not isinstance(path, str):
        return False

    # Check for mixed format (contains .task/)
    if ".task/" in path:
        return True

    # Check for direct format (UUID/path)
    # UUID format: 32 hex chars with optional hyphens
    if "/" in path:
        first_part = path.split("/", 1)[0]
        # Remove hyphens and check if it's a valid UUID
        uuid_candidate = first_part.replace("-", "")
        if len(uuid_candidate) == 32 and all(c in "0123456789abcdefABCDEF" for c in uuid_candidate):
            return True

    return False


def parse_task_resource_path(path: str) -> tuple[str, str, str]:
    """Parse mixed catalog/TaskResource path.

    Args:
        path: Mixed path like "john_doe:Projects/Folder/test.task/src/utils"

    Returns:
        Tuple of (catalog_path, task_name, internal_path)
        Example: ("john_doe:Projects/Folder", "test.task", "src/utils")

    Raises:
        ValueError: If path doesn't contain .task/ segment

    Examples:
        >>> parse_task_resource_path("john_doe:Projects/test.task/src/utils")
        ("john_doe:Projects", "test.task", "src/utils")

        >>> parse_task_resource_path("john_doe:Projects/Folder/my_task.task/scripts")
        ("john_doe:Projects/Folder", "my_task.task", "scripts")

        >>> parse_task_resource_path("john_doe:Projects/test.task")
        ("john_doe:Projects", "test.task", "")
    """
    if ".task/" not in path and not path.endswith(".task"):
        raise ValueError(
            f"Path '{path}' does not contain .task/ segment. "
            "Expected format: 'owner:folder/task.task/internal/path'"
        )

    # Find .task boundary
    if ".task/" in path:
        # Split on .task/
        before_task, after_task = path.split(".task/", 1)
        internal_path = after_task
    else:
        # Path ends with .task (no internal path)
        before_task = path[:-5]  # Remove .task
        internal_path = ""

    # Split catalog path and task name
    # Find last / before .task
    if "/" in before_task:
        catalog_path, task_name = before_task.rsplit("/", 1)
        task_name = task_name + ".task"
    else:
        # Edge case: "owner:.task" or just task name
        catalog_path = before_task
        task_name = ".task"

    return catalog_path, task_name, internal_path


def resolve_task_resource_by_path(client: Client, catalog_path: str, task_name: str) -> str:
    """Find TaskResource by catalog path and name.

    Args:
        client: EverGIS API client
        catalog_path: Catalog path to parent folder (e.g., "john_doe:Projects/Folder")
        task_name: TaskResource name (e.g., "test.task" or "test")

    Returns:
        TaskResource UUID (resourceId)

    Raises:
        ValueError: If TaskResource not found or not unique

    Example:
        >>> task_id = resolve_task_resource_by_path(
        ...     client, "john_doe:Projects", "test.task"
        ... )
        >>> print(task_id)
        '6c02301ae0b94cf8a6f595b20890b1b7'
    """
    # Resolve parent folder
    parent_folder = get_or_create_folder_by_path(client, catalog_path)

    # Get children resources using post_get_all
    resource_request = ListResourcesDc(parentId=parent_folder.resourceId)
    resources_response = client.catalog.post_get_all(body=resource_request)
    resources = resources_response.items

    # Normalize task name (remove .task extension if present)
    task_name_normalized = task_name.replace(".task", "")

    # Find TaskResource with matching name
    matching_tasks = []
    for resource in resources:
        if resource.type == CatalogResourceType.TASKPROTOTYPE:
            # Check both with and without .task extension
            resource_name_normalized = resource.name.replace(".task", "")
            if resource_name_normalized == task_name_normalized:
                matching_tasks.append(resource)

    if not matching_tasks:
        raise ValueError(f"TaskResource '{task_name}' not found in catalog path '{catalog_path}'")

    if len(matching_tasks) > 1:
        raise ValueError(
            f"Multiple TaskResources with name '{task_name}' found in '{catalog_path}'. "
            "Please ensure unique names."
        )

    return matching_tasks[0].resourceId


def create_folder_in_task_resource(
    client: Client,
    task_resource_id: str,
    folder_path: str,
    *,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> str:
    """Create nested folders inside TaskResource (always creates new folders).

    Creates folder hierarchy within TaskResource using special parentId format.
    WARNING: This function always creates new folders and will fail if they exist.
    Use get_or_create_folder_in_task_resource() to check existence first.

    The parentId format for TaskResource internal folders is: "taskId/path/to/parent"

    Args:
        client: EverGIS API client
        task_resource_id: TaskResource UUID
        folder_path: Internal path like "src/utils" (relative to TaskResource root)
        description: Optional description for the final folder only
        tags: Optional tags for the final folder only

    Returns:
        Final parentId string for file uploads (e.g., "taskId/src/utils")

    Raises:
        ApiClientError: If folder already exists (HTTP 409)
        Exception: If folder creation fails

    Examples:
        >>> # Create src/utils inside TaskResource
        >>> parent_id = create_folder_in_task_resource(
        ...     client,
        ...     task_resource_id="6c02301ae0b94cf8a6f595b20890b1b7",
        ...     folder_path="src/utils",
        ... )
        >>> print(parent_id)
        '6c02301ae0b94cf8a6f595b20890b1b7/src/utils'
    """
    if not folder_path or not folder_path.strip():
        # No internal path, return task root
        return task_resource_id

    # Split into segments
    segments = [seg.strip() for seg in folder_path.split("/") if seg.strip()]

    if not segments:
        return task_resource_id

    # Get user for folder ownership
    user_info = client.account.get_user_info()
    owner = user_info.username

    # Build folders sequentially
    current_parent_id = task_resource_id

    for i, folder_name in enumerate(segments):
        is_final = i == len(segments) - 1

        # Apply description and tags only to final folder
        folder_description = description if is_final else None
        folder_tags = tags if is_final else None

        # Create folder with TaskResource parentId format
        create_folder(
            client=client,
            name=folder_name,
            parent_id=current_parent_id,
            description=folder_description,
            tags=folder_tags,
            owner=owner,
        )

        # Build next parent_id in TaskResource format
        if i == 0:
            # First level: taskId/folder_name
            current_parent_id = f"{task_resource_id}/{folder_name}"
        else:
            # Subsequent levels: taskId/path/to/folder_name
            current_parent_id = f"{current_parent_id}/{folder_name}"

    return current_parent_id


def get_or_create_folder_in_task_resource(
    client: Client,
    task_resource_id: str,
    folder_path: str,
    *,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> str:
    """Get or create nested folders inside TaskResource.

    Checks for existing folders before creating new ones. This is the recommended
    function to use for TaskResource folder operations.

    Args:
        client: EverGIS API client
        task_resource_id: TaskResource UUID
        folder_path: Internal path like "src/utils" (relative to TaskResource root)
        description: Optional description for the final folder (used only when creating)
        tags: Optional tags for the final folder (used only when creating)

    Returns:
        Final parentId string for file uploads (e.g., "taskId/src/utils")

    Examples:
        >>> # Get or create src/utils inside TaskResource
        >>> parent_id = get_or_create_folder_in_task_resource(
        ...     client,
        ...     task_resource_id="6c02301ae0b94cf8a6f595b20890b1b7",
        ...     folder_path="src/utils",
        ... )
        >>> # Rerun - will find existing folder instead of creating
        >>> parent_id = get_or_create_folder_in_task_resource(
        ...     client,
        ...     task_resource_id="6c02301ae0b94cf8a6f595b20890b1b7",
        ...     folder_path="src/utils",
        ... )
    """
    if not folder_path or not folder_path.strip():
        return task_resource_id

    segments = [seg.strip() for seg in folder_path.split("/") if seg.strip()]
    if not segments:
        return task_resource_id

    # Get user for folder ownership
    user_info = client.account.get_user_info()
    owner = user_info.username

    # Build folders sequentially, checking existence
    current_parent_id = task_resource_id

    for i, folder_name in enumerate(segments):
        is_final = i == len(segments) - 1

        # Check if folder exists
        resource_request = ListResourcesDc(parentId=current_parent_id)
        resources_response = client.catalog.post_get_all(body=resource_request)

        existing_folder = None
        for resource in resources_response.items:
            if resource.name == folder_name and resource.type == CatalogResourceType.DIRECTORY:
                existing_folder = resource
                break

        if existing_folder:
            # Folder exists, use it
            # Build TaskResource format path
            if i == 0:
                current_parent_id = f"{task_resource_id}/{folder_name}"
            else:
                current_parent_id = f"{current_parent_id}/{folder_name}"
        else:
            # Folder doesn't exist, create it
            folder_description = description if is_final else None
            folder_tags = tags if is_final else None

            create_folder(
                client=client,
                name=folder_name,
                parent_id=current_parent_id,
                description=folder_description,
                tags=folder_tags,
                owner=owner,
            )

            # Build next parent_id in TaskResource format
            if i == 0:
                current_parent_id = f"{task_resource_id}/{folder_name}"
            else:
                current_parent_id = f"{current_parent_id}/{folder_name}"

    return current_parent_id


def upload_file_to_task_resource(
    client: Client,
    file_path: Union[str, Path],
    task_resource_id: str,
    internal_path: str = "",
    *,
    owner: Optional[str] = None,
    rewrite: bool = True,
    description: Optional[str] = None,
) -> CatalogResourceDc:
    """Upload file to TaskResource.

    Convenience wrapper that creates internal folders if needed and uploads file.

    Args:
        client: EverGIS API client
        file_path: Local file path to upload
        task_resource_id: TaskResource UUID
        internal_path: Internal path like "src/utils" (creates folders if needed)
        owner: Optional owner (defaults to current user)
        rewrite: If True, overwrites existing file with same name
        description: Optional file description

    Returns:
        CatalogResourceDc for the uploaded file

    Raises:
        FileNotFoundError: If local file doesn't exist
        Exception: If upload fails

    Examples:
        >>> # Upload to TaskResource root
        >>> result = upload_file_to_task_resource(
        ...     client,
        ...     file_path="script.py",
        ...     task_resource_id="6c02301ae0b94cf8a6f595b20890b1b7",
        ... )

        >>> # Upload to internal folder (creates if needed)
        >>> result = upload_file_to_task_resource(
        ...     client,
        ...     file_path="utils.py",
        ...     task_resource_id="6c02301ae0b94cf8a6f595b20890b1b7",
        ...     internal_path="src/utils",
        ... )
    """
    # Import here to avoid circular dependency
    from .files import upload_file

    # Get or create internal folders if needed
    if internal_path and internal_path.strip():
        parent_id = get_or_create_folder_in_task_resource(client, task_resource_id, internal_path)
    else:
        parent_id = task_resource_id

    # Upload file using parent_id
    return upload_file(
        client=client,
        file_path=file_path,
        parent_id=parent_id,
        owner=owner,
        rewrite=rewrite,
        description=description,
    )
