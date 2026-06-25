"""Folder management utilities for EverGIS catalog."""

from __future__ import annotations

from typing import List, Optional

from evergis_api import Client
from evergis_api.schemas import CatalogResourceDc, CatalogResourceType, ListResourcesDc

from .._errors import ResourceNotFound, raise_conflict_as_exists
from .resources import resolve_resource


def is_container(resource: CatalogResourceDc) -> bool:
    """Check if a resource can contain child elements.

    A resource is a container if it has isObservable=True. This includes:
    - DIRECTORY (folders)
    - MAP (maps)
    - LAYER (layers with child layers/tables)
    - TASKPROTOTYPE (task prototypes)

    Args:
        resource: Resource to check

    Returns:
        True if the resource can contain child elements

    Example:
        >>> folder = client.catalog.get_catalog_resource(folder_id)
        >>> if is_container(folder):
        ...     print("Can add child resources")
    """
    return resource.isObservable is True


# What child types are allowed inside each container type.
#
# Symlinks (created via ``post_link``) do not have their own
# ``CatalogResourceType`` value - they take the type of their target,
# so symlink validity is governed by the target's type entry below.
# DataSource follows the same rules as Layer/Table for permissiveness.
_CONTAINMENT_RULES: dict[
    CatalogResourceType, frozenset[CatalogResourceType]
] = {
    CatalogResourceType.DIRECTORY: frozenset(CatalogResourceType),
    # Map accepts everything except another Map.
    CatalogResourceType.MAP: frozenset(
        t for t in CatalogResourceType if t != CatalogResourceType.MAP
    ),
    # Layer accepts files, folders, tables, task prototypes, data sources -
    # but not another Map or Layer.
    CatalogResourceType.LAYER: frozenset(
        {
            CatalogResourceType.DIRECTORY,
            CatalogResourceType.TABLE,
            CatalogResourceType.FILE,
            CatalogResourceType.TASKPROTOTYPE,
            CatalogResourceType.DATASOURCE,
        }
    ),
    # TaskPrototype accepts only folders and files.
    CatalogResourceType.TASKPROTOTYPE: frozenset(
        {CatalogResourceType.DIRECTORY, CatalogResourceType.FILE}
    ),
}


def can_contain(
    parent: CatalogResourceDc, child_type: Optional[CatalogResourceType] = None
) -> bool:
    """Check if a parent resource can contain a specific child type.

    Container rules (as enforced by the EverGIS catalog server):

    * ``Directory``     - any child type.
    * ``Map``           - any child type **except** another ``Map``.
    * ``Layer``         - ``Directory``, ``Table``, ``File``,
      ``TaskPrototype``, ``DataSource``. **Not** ``Map`` or ``Layer``.
    * ``TaskPrototype`` - ``Directory`` and ``File`` only.

    Symlinks created via ``post_link`` carry the type of their target,
    so this check applies to the target type as well.

    Args:
        parent: Parent resource.
        child_type: Optional child resource type for strict validation.
            If omitted, the function only verifies that ``parent`` is
            an observable container.

    Returns:
        True if ``parent`` can contain ``child_type`` (or, with
        ``child_type=None``, if ``parent`` is a container at all).

    Examples:
        >>> can_contain(some_resource)
        True
        >>> can_contain(map_resource, CatalogResourceType.LAYER)
        True
        >>> can_contain(map_resource, CatalogResourceType.MAP)
        False
        >>> can_contain(taskprototype, CatalogResourceType.LAYER)
        False
    """
    if not is_container(parent):
        return False
    if child_type is None:
        return True
    return child_type in _CONTAINMENT_RULES.get(parent.type, frozenset())


def is_valid_path_container(resource: CatalogResourceDc) -> bool:
    """Check if a resource can be part of a catalog path for folder operations.

    Valid path containers are resources that can contain children AND are supported
    in path-based folder creation/resolution.

    Valid types:
    - DIRECTORY (folders)
    - MAP (maps)
    - LAYER (layers with child layers/tables)

    TASKPROTOTYPE is excluded as it has different path resolution logic.

    Args:
        resource: Resource to check

    Returns:
        True if the resource can be part of catalog paths

    Example:
        >>> map_resource = client.catalog.get_catalog_resource(map_id)
        >>> if is_valid_path_container(map_resource):
        ...     # Can use in path operations
        ...     folder = get_or_create_folder_by_path(client, "owner/MyMap/SubFolder")
    """
    if not is_container(resource):
        return False

    # TASKPROTOTYPE is not valid for path-based folder creation
    return resource.type != CatalogResourceType.TASKPROTOTYPE


def create_folder(
    client: Client,
    name: str,
    parent_id: Optional[str] = None,
    *,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    owner: Optional[str] = None,
) -> CatalogResourceDc:
    """Create a new folder in the catalog.

    Args:
        client: EverGIS API client
        name: Name of the folder to create
        parent_id: ID of the parent folder/resource
        description: Optional description for the folder
        tags: Optional list of tags for the folder
        owner: Optional owner of the folder (defaults to current user)

    Returns:
        CatalogResourceDc: The created folder resource

    Raises:
        Exception: If folder creation fails

    Example:
        >>> from evergis_api import Client
        >>> from evergis_tools.catalog import create_folder
        >>>
        >>> client = Client(base_url="https://api.example.com", sb_token="token")
        >>> folder = create_folder(
        ...     client=client,
        ...     name="My Data Folder",
        ...     parent_id="parent_folder_id",
        ...     description="Folder for storing 2GIS data",
        ...     tags=["2GIS", "data"]
        ... )
        >>> print(f"Created folder: {folder.name}")
    """
    if owner is None:
        user_info = client.account.get_user_info()
        owner = user_info.username

    folder_data = CatalogResourceDc(
        name=name, parentId=parent_id, description=description, tags=tags or [], owner=owner
    )

    try:
        return client.catalog.create_directory(folder_data)
    except Exception as e:
        raise_conflict_as_exists(e, resource=f"folder {name!r}")
        raise


def create_nested_folders(
    client: Client,
    folder_path: str,
    parent_id: str,
    *,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    owner: Optional[str] = None,
) -> List[CatalogResourceDc]:
    """Create nested folders from a path.

    Args:
        client: EverGIS API client
        folder_path: Path-like string with folders separated by '/' (e.g., "data/2gis/cities")
        parent_id: ID of the root parent folder/resource
        description: Optional description for the final folder
        tags: Optional list of tags for the final folder
        owner: Optional owner of the folders (defaults to current user)

    Returns:
        List[CatalogResourceDc]: List of created folders (leaf to root)

    Example:
        >>> folders = create_nested_folders(
        ...     client=client,
        ...     folder_path="data/2gis/cities",
        ...     parent_id="root_id",
        ...     tags=["data", "2gis"]
        ... )
        >>> print(f"Created {len(folders)} folders")
    """
    if owner is None:
        user_info = client.account.get_user_info()
        owner = user_info.username

    created_folders = []
    current_parent_id = parent_id

    # Split path and create folders sequentially
    folder_names = [name.strip() for name in folder_path.split("/") if name.strip()]

    for i, folder_name in enumerate(folder_names):
        # Apply description and tags only to the final folder
        is_final = i == len(folder_names) - 1
        folder_description = description if is_final else None
        folder_tags = tags if is_final else None

        folder = create_folder(
            client=client,
            name=folder_name,
            parent_id=current_parent_id,
            description=folder_description,
            tags=folder_tags,
            owner=owner,
        )

        created_folders.append(folder)
        current_parent_id = folder.resourceId

    return created_folders


def find_folder_by_name(
    client: Client, folder_name: str, parent_id: Optional[str] = None
) -> Optional[CatalogResourceDc]:
    """Find a container (folder/map/taskprototype) by name in the catalog.

    Searches for any container resource (DIRECTORY, MAP, LAYER, TASKPROTOTYPE)
    with the specified name.

    Args:
        client: EverGIS API client
        folder_name: Name of the container to find
        parent_id: Optional parent container ID to search within

    Returns:
        CatalogResourceDc or None: The found container or None if not found

    Example:
        >>> folder = find_folder_by_name(client, "My Data Folder", parent_id="parent_id")
        >>> if folder:
        ...     print(f"Found container: {folder.resourceId} (type: {folder.type})")
        ... else:
        ...     print("Container not found")
    """
    # None strictly means "no container with that name"; listing failures
    # (network, 5xx) propagate instead of masquerading as "not found"
    if parent_id:
        resource_request = ListResourcesDc(parentId=parent_id)
    else:
        resource_request = ListResourcesDc()

    resources_response = client.catalog.post_get_all(body=resource_request)

    for resource in resources_response.items or []:
        if resource.name == folder_name and is_container(resource):
            return resource

    return None


def get_or_create_folder(
    client: Client,
    name: str,
    parent_id: str,
    *,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    owner: Optional[str] = None,
) -> CatalogResourceDc:
    """Get existing folder or create new one if it doesn't exist.

    Args:
        client: EverGIS API client
        name: Name of the folder
        parent_id: ID of the parent folder/resource
        description: Optional description for the folder (used only when creating)
        tags: Optional list of tags for the folder (used only when creating)
        owner: Optional owner of the folder (defaults to current user)

    Returns:
        CatalogResourceDc: The existing or newly created folder

    Example:
        >>> folder = get_or_create_folder(
        ...     client=client,
        ...     name="Data Folder",
        ...     parent_id="parent_id",
        ...     description="Auto-created folder"
        ... )
        >>> print(f"Folder ID: {folder.resourceId}")
    """
    # Try to find existing folder
    existing_folder = find_folder_by_name(client, name, parent_id)
    if existing_folder:
        return existing_folder

    # Create new folder if not found
    return create_folder(
        client=client,
        name=name,
        parent_id=parent_id,
        description=description,
        tags=tags,
        owner=owner,
    )


def get_or_create_nested_folders(
    client: Client,
    folder_path: str,
    parent_id: str,
    *,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    owner: Optional[str] = None,
) -> CatalogResourceDc:
    """Get or create nested folders from a path, returning the final folder.

    Args:
        client: EverGIS API client
        folder_path: Path-like string with folders separated by '/' (e.g., "data/2gis/cities")
        parent_id: ID of the root parent folder/resource
        description: Optional description for the final folder
        tags: Optional list of tags for the final folder
        owner: Optional owner of the folders (defaults to current user)

    Returns:
        CatalogResourceDc: The final folder in the path

    Example:
        >>> final_folder = get_or_create_nested_folders(
        ...     client=client,
        ...     folder_path="data/2gis/cities",
        ...     parent_id="root_id"
        ... )
        >>> print(f"Final folder ID: {final_folder.resourceId}")
    """
    if owner is None:
        user_info = client.account.get_user_info()
        owner = user_info.username

    current_parent_id = parent_id
    folder_names = [name.strip() for name in folder_path.split("/") if name.strip()]

    for i, folder_name in enumerate(folder_names):
        # Apply description and tags only to the final folder
        is_final = i == len(folder_names) - 1
        folder_description = description if is_final else None
        folder_tags = tags if is_final else None

        folder = get_or_create_folder(
            client=client,
            name=folder_name,
            parent_id=current_parent_id,
            description=folder_description,
            tags=folder_tags,
            owner=owner,
        )

        current_parent_id = folder.resourceId

    # Return the final folder
    return folder


def get_or_create_folder_by_path(
    client: Client,
    path: str,
    *,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
) -> CatalogResourceDc:
    """
    Get existing container or create folder hierarchy by catalog path.

    Recursively resolves path segments from right to left, finding the deepest
    existing parent container, then creates missing folders as needed.

    Supported path container types: DIRECTORY, MAP, LAYER.
    TASKPROTOTYPE is excluded as it has different path resolution logic.
    Always creates DIRECTORY resources for missing path segments.

    Args:
        client: Initialized EverGIS API client
        path: Catalog path (e.g., "owner/Projects/Data/My project")
        description: Optional description for the final folder (used only when creating)
        tags: Optional list of tags for the final folder (used only when creating)

    Returns:
        CatalogResourceDc for the final container with path field set

    Raises:
        ValueError: If path format is invalid, path exists but is not a valid container,
                   or no parent container is accessible for creation

    Examples:
        >>> from evergis_api import Client
        >>> from evergis_tools.catalog.folders import get_or_create_folder_by_path
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>>
        >>> # Get or create nested folder structure
        >>> folder = get_or_create_folder_by_path(
        ...     client,
        ...     "owner/Projects/Data/My project",
        ...     description="My project data",
        ...     tags=["project", "data"]
        ... )
        >>> print(f"Folder ID: {folder.resourceId}")
        >>> print(f"Folder path: {folder.path}")
    """
    if not isinstance(path, str):
        raise ValueError(f"path must be str, got {type(path).__name__}")

    path = path.strip()

    if not path:
        raise ValueError("path cannot be empty")

    if ":" not in path and "/" not in path:
        raise ValueError(
            f"Invalid catalog path format '{path}'. Expected "
            "'owner:folder/subfolder/...' or 'owner/folder/subfolder/...'"
        )

    # Try to resolve the full path first
    try:
        resource_obj = resolve_resource(client, path)

        # Check if it's a valid path container (excludes TASKPROTOTYPE)
        if not is_valid_path_container(resource_obj):
            raise ValueError(
                f"Path '{path}' exists but is not a valid path container (type: {resource_obj.type})"
            )

        # Set the path explicitly and return
        resource_obj.path = path
        return resource_obj
    except ResourceNotFound:
        # Path doesn't exist - continue to create. A genuine "exists but
        # not a container" ValueError (above) propagates instead of being
        # mistaken for "not found".
        pass

    # Split owner from folder segments. Accept both the legacy
    # 'owner:rest' form and the v3 'owner/rest' path form; the
    # candidate-path probes below use the colon form, which
    # ``resolve_resource`` normalises back to a slash path.
    if ":" in path:
        owner_part, _, folder_path = path.partition(":")
    else:
        owner_part, _, folder_path = path.partition("/")
    if not owner_part or not folder_path:
        raise ValueError(
            f"Invalid catalog path format '{path}'. Expected "
            "'owner:folder/subfolder/...' or 'owner/folder/subfolder/...'"
        )

    folder_segments = [seg.strip() for seg in folder_path.split("/") if seg.strip()]

    if not folder_segments:
        raise ValueError(f"No folder segments found in path '{path}'")

    # Find the deepest existing parent by trying progressively shorter paths
    parent_resource = None
    parent_path = None
    start_index = 0

    # Find the deepest existing parent folder, trying progressively
    # shorter paths down to (but not including) the owner root. The root
    # is not a resolvable resource - top-level resources have
    # parentId=None - so when no intermediate folder resolves we create
    # from the root with no parent.
    for i in range(len(folder_segments) - 1, 0, -1):
        candidate_path = f"{owner_part}/{'/'.join(folder_segments[:i])}"
        try:
            parent_resource = resolve_resource(client, candidate_path)

            # Check if it's a valid path container
            if not is_valid_path_container(parent_resource):
                raise ValueError(
                    f"Parent path '{candidate_path}' exists but is not a valid path container (type: {parent_resource.type})"
                )

            parent_path = candidate_path
            start_index = i
            break
        except ResourceNotFound:
            # This level doesn't exist, try next level up. "Exists but not a
            # container" (above) propagates instead of being skipped.
            continue

    # No existing intermediate folder -> create from the catalog root
    # (parentId=None). parent_resource stays None in that case.
    current_parent_id = parent_resource.resourceId if parent_resource else None
    current_path = parent_path if parent_path else owner_part

    # Get owner for folder creation
    user_info = client.account.get_user_info()
    owner = user_info.username

    for i in range(start_index, len(folder_segments)):
        folder_name = folder_segments[i]
        is_final = i == len(folder_segments) - 1

        # Build the full path for this folder (slash form).
        current_path = f"{current_path}/{folder_name}"

        # Try to get existing folder at this level
        try:
            folder_resource = resolve_resource(client, current_path)

            # Check if it's a valid path container
            if not is_valid_path_container(folder_resource):
                raise ValueError(
                    f"Path '{current_path}' exists but is not a valid path container (type: {folder_resource.type})"
                )

            current_parent_id = folder_resource.resourceId

            # If this is the final folder, set metadata and return
            if is_final:
                folder_resource.path = path
                return folder_resource
        except ResourceNotFound:
            # Folder doesn't exist, create it
            folder_description = description if is_final else None
            folder_tags = tags if is_final else None

            folder_resource = create_folder(
                client=client,
                name=folder_name,
                parent_id=current_parent_id,
                description=folder_description,
                tags=folder_tags,
                owner=owner,
            )

            current_parent_id = folder_resource.resourceId

            # If this is the final folder, set path and return
            if is_final:
                folder_resource.path = path
                return folder_resource

    # This should never be reached, but just in case
    raise ValueError(f"Failed to create or retrieve folder at path '{path}'")
