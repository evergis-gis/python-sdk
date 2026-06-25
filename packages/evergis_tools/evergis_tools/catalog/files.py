"""File upload utilities for EverGIS catalog."""

import logging
from pathlib import Path
from typing import List, Optional, Union

from evergis_api import Client
from evergis_api._generated.schemas import CatalogResourceDc
from evergis_api.schemas import (
    CatalogResourceType,
    ConflictResolutionStrategy,
    ZipExtractRequestDc,
)
from evergis_tools._errors import raise_conflict_as_exists
from evergis_tools.catalog.folders import get_or_create_folder_by_path
from evergis_tools.catalog.resources import resolve_resource

logger = logging.getLogger(__name__)


def upload_file(
    client: Client,
    file_path: Union[str, Path],
    parent_path: Optional[str] = None,
    *,
    parent_id: Optional[str] = None,
    owner: Optional[str] = None,
    rewrite: bool = True,
    description: Optional[str] = None,
) -> CatalogResourceDc:
    """Upload a single file to EverGIS catalog or TaskResource.

    Supports multiple upload targets:
    - Regular catalog paths: "john_doe:Projects/Data"
    - TaskResource mixed paths: "john_doe:Projects/test.task/src/utils" (auto-detected)
    - Direct parent_id: Resource UUID or TaskResource format "taskId/internal/path"

    Args:
        client: EverGIS API client
        file_path: Path to the file to upload
        parent_path: Catalog path for parent folder. Mutually exclusive with parent_id.
                    - Regular: "john_doe:Projects/Data"
                    - TaskResource: "john_doe:Projects/test.task/src/utils"
                    If the path doesn't exist, folders will be created automatically.
        parent_id: Direct parent resource ID. Mutually exclusive with parent_path.
                   Supports TaskResource format: "taskId/internal/path"
        owner: Owner of the file (defaults to current user)
        rewrite: Whether to overwrite existing files
        description: Optional description for the file

    Returns:
        CatalogResourceDc: Information about the uploaded file

    Raises:
        FileNotFoundError: If the file doesn't exist
        ValueError: If neither parent_path nor parent_id specified, or both specified
        Exception: If upload fails

    Examples:
        >>> from evergis_api import Client
        >>> from evergis_tools.catalog.files import upload_file
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>>
        >>> # Upload to regular catalog path
        >>> result = upload_file(
        ...     client=client,
        ...     file_path="data.zip",
        ...     parent_path="john_doe:Projects/Data"
        ... )
        >>>
        >>> # Upload to TaskResource (auto-detected mixed path)
        >>> result = upload_file(
        ...     client=client,
        ...     file_path="script.py",
        ...     parent_path="john_doe:Projects/test.task/src/utils"
        ... )
        >>>
        >>> # Upload using direct parent_id
        >>> result = upload_file(
        ...     client=client,
        ...     file_path="script.py",
        ...     parent_id="6c02301ae0b94cf8a6f595b20890b1b7/src"
        ... )
    """
    file_path = Path(file_path)

    if not file_path.is_file():
        raise FileNotFoundError(f"File not found: {file_path}")

    # Validate mutually exclusive parameters
    if not parent_path and not parent_id:
        raise ValueError("Either parent_path or parent_id must be specified")
    if parent_path and parent_id:
        raise ValueError(
            "Cannot specify both parent_path and parent_id. "
            "Use parent_path for catalog paths or parent_id for direct resource IDs."
        )

    # Determine actual parent_id based on provided parameters
    if parent_id:
        # Direct parent_id (includes TaskResource format "taskId/path")
        actual_parent_id = parent_id

    elif parent_path:
        # Import TaskResource utilities
        from .task_resources import (
            is_task_resource_path,
            parse_task_resource_path,
            resolve_task_resource_by_path,
            get_or_create_folder_in_task_resource,
        )

        if is_task_resource_path(parent_path):
            # TaskResource mixed path: "john_doe:Projects/test.task/src/utils"
            catalog_path, task_name, internal_path = parse_task_resource_path(parent_path)

            # Resolve TaskResource ID
            task_id = resolve_task_resource_by_path(client, catalog_path, task_name)

            # Get or create internal folders if needed
            if internal_path:
                actual_parent_id = get_or_create_folder_in_task_resource(
                    client, task_id, internal_path
                )
            else:
                actual_parent_id = task_id
        else:
            # Regular catalog path: "john_doe:Projects/Data"
            folder = get_or_create_folder_by_path(client=client, path=parent_path)
            actual_parent_id = folder.resourceId

    # Get current user if owner not specified
    if owner is None:
        owner = client.account.get_user_info().username

    # Set description if not provided
    if description is None:
        description = f"Uploaded file: {file_path.name}"

    # Upload file using binary stream
    with file_path.open("rb") as f:
        return client.catalog.create_file_1(
            file=f,
            fileName=file_path.name,
            parentId=actual_parent_id,
            owner=owner,
            rewrite=rewrite,
            description=description,
            url=None,
        )


def upload_files_by_extension(
    client: Client,
    directory_path: Union[str, Path],
    parent_path: str,
    extensions: Optional[Union[str, List[str]]] = None,
    *,
    owner: Optional[str] = None,
    rewrite: bool = True,
    recursive: bool = False,
) -> List[CatalogResourceDc]:
    """Upload files with specified extensions from a directory.

    Args:
        client: EverGIS API client
        directory_path: Path to the directory to scan
        parent_path: Catalog path for parent folder (e.g., "owner/Projects/Data").
                    If the path doesn't exist, all missing folders will be created automatically.
        extensions: File extension(s) to upload (e.g., '.zip' or ['.zip', '.shp']).
                   If None or ['*'], uploads all files.
        owner: Owner of the files (defaults to current user)
        rewrite: Whether to overwrite existing files
        recursive: Whether to scan subdirectories

    Returns:
        List[CatalogResourceDc]: Information about uploaded files

    Raises:
        FileNotFoundError: If directory doesn't exist
        ValueError: If parent path is invalid

    Example:
        >>> from evergis_api import Client
        >>> from evergis_tools.catalog.files import upload_files_by_extension
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>>
        >>> # Upload all .zip files to existing or new folder (automatically created)
        >>> results = upload_files_by_extension(
        ...     client=client,
        ...     directory_path="./data",
        ...     parent_path="owner/Projects/Archives",
        ...     extensions=".zip"
        ... )
        >>> print(f"Uploaded {len(results)} files")
    """
    directory_path = Path(directory_path)

    if not directory_path.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    # Get or create parent folder (validate once, not for each file)
    # We call this once to ensure folder exists before uploading files
    get_or_create_folder_by_path(client=client, path=parent_path)

    # Handle all files case
    if extensions is None or extensions == "*" or extensions == ["*"]:
        files = _find_all_files(directory_path, recursive)
    else:
        # Normalize extensions
        if isinstance(extensions, str):
            extensions = [extensions]

        extensions = [
            ext.lower() if ext.startswith(".") else f".{ext.lower()}" for ext in extensions
        ]

        # Find files
        files = _find_files_by_extension(directory_path, extensions, recursive)

    # Upload files; a single bad file must not abort the whole batch,
    # but a fully failed batch is an error, not an empty success
    results = []
    failures = []
    for file_path in files:
        try:
            result = upload_file(
                client=client,
                file_path=file_path,
                parent_path=parent_path,
                owner=owner,
                rewrite=rewrite,
            )
            results.append(result)
            logger.info(f"Uploaded {result.name} ({result.resourceId})")
        except Exception as e:
            failures.append(file_path.name)
            logger.error(f"Failed to upload {file_path.name}: {e}")

    if files and not results:
        raise RuntimeError(
            f"All {len(failures)} file uploads to '{parent_path}' failed; "
            f"first failures: {failures[:5]}"
        )
    return results


def _find_all_files(directory: Path, recursive: bool = False) -> List[Path]:
    """Find all files in directory.

    Args:
        directory: Directory to search
        recursive: Whether to search subdirectories

    Returns:
        List of all file paths
    """
    files = []

    if recursive:
        for file_path in directory.rglob("*"):
            if file_path.is_file():
                files.append(file_path)
    else:
        for file_path in directory.iterdir():
            if file_path.is_file():
                files.append(file_path)

    return sorted(files)


def _find_files_by_extension(
    directory: Path, extensions: List[str], recursive: bool = False
) -> List[Path]:
    """Find files with specified extensions in directory.

    Args:
        directory: Directory to search
        extensions: List of extensions to match
        recursive: Whether to search subdirectories

    Returns:
        List of matching file paths
    """
    files = []

    if recursive:
        for file_path in directory.rglob("*"):
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                files.append(file_path)
    else:
        for file_path in directory.iterdir():
            if file_path.is_file() and file_path.suffix.lower() in extensions:
                files.append(file_path)

    return sorted(files)


def _collect_remote_resources(
    client: Client, parent_id: str, base_path: str = ""
) -> dict[str, CatalogResourceDc]:
    """Recursively collect all remote resources from a parent folder.

    Args:
        client: EverGIS API client
        parent_id: Parent resource ID (supports TaskResource format "taskId/path")
        base_path: Base path for building relative paths (internal use)

    Returns:
        Dict mapping relative paths to CatalogResourceDc objects
    """
    from evergis_api._generated.schemas import ListResourcesDc

    resources = {}

    # Get all children of this parent
    response = client.catalog.post_get_all(ListResourcesDc(parentId=parent_id))
    children = response.items

    for child in children:
        # Build relative path
        if base_path:
            rel_path = f"{base_path}/{child.name}"
        else:
            rel_path = child.name

        resources[rel_path] = child

        # Recursively collect from directories
        if child.type == CatalogResourceType.DIRECTORY:
            # For TaskResource, use taskId/internal/path format
            if "/" in parent_id:  # TaskResource format
                child_id = f"{parent_id}/{child.name}"
            else:
                child_id = child.resourceId

            child_resources = _collect_remote_resources(client, child_id, rel_path)
            resources.update(child_resources)

    return resources


def upload_directory(
    client: Client,
    directory_path: Union[str, Path],
    parent_path: str,
    *,
    owner: Optional[str] = None,
    rewrite: bool = True,
    ignore_patterns: Optional[List[str]] = None,
    sync: bool = False,
) -> List[CatalogResourceDc]:
    """Upload entire directory to EverGIS catalog, preserving structure.

    Recursively uploads all files from a directory while maintaining the folder
    hierarchy. Supports ignore patterns similar to .gitignore.

    Args:
        client: EverGIS API client
        directory_path: Path to the directory to upload
        parent_path: Target catalog path (e.g., "john_doe:Projects/Data" or "john_doe:Projects/task.task/src")
                    Supports both regular catalog paths and TaskResource paths.
        owner: Optional owner (defaults to current user)
        rewrite: Whether to overwrite existing files
        ignore_patterns: Optional list of patterns to ignore (e.g., ["__pycache__", "*.pyc"])
                        If None, uses default patterns.
        sync: If True, delete remote files and folders that don't exist locally (like rsync)

    Returns:
        List[CatalogResourceDc]: Information about uploaded files

    Raises:
        FileNotFoundError: If directory doesn't exist
        ValueError: If parent_path is invalid

    Default ignore patterns:
        - __pycache__
        - *.pyc, *.pyo, *.pyd
        - .DS_Store, ._.DS_Store
        - Thumbs.db
        - *.tmp, *.swp, *~

    Examples:
        >>> from evergis_api import Client
        >>> from evergis_tools.catalog import upload_directory
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>>
        >>> # Upload to regular catalog path
        >>> results = upload_directory(
        ...     client=client,
        ...     directory_path="./my_project/src",
        ...     parent_path="john_doe:Projects/Data"
        ... )
        >>> print(f"Uploaded {len(results)} files")
        >>>
        >>> # Upload with sync (delete remote files not in local)
        >>> results = upload_directory(
        ...     client=client,
        ...     directory_path="./scripts",
        ...     parent_path="john_doe:Projects/Data",
        ...     sync=True
        ... )
        >>>
        >>> # Upload to TaskResource with custom ignore patterns
        >>> results = upload_directory(
        ...     client=client,
        ...     directory_path="./scripts",
        ...     parent_path="john_doe:Projects/test.task/src",
        ...     ignore_patterns=["*.log", "temp/"],
        ...     sync=True
        ... )
    """
    import fnmatch

    directory_path = Path(directory_path)

    if not directory_path.is_dir():
        raise FileNotFoundError(f"Directory not found: {directory_path}")

    # Default ignore patterns (like .gitignore)
    if ignore_patterns is None:
        ignore_patterns = [
            "__pycache__",
            "*.pyc",
            "*.pyo",
            "*.pyd",
            ".DS_Store",
            "._.DS_Store",
            "Thumbs.db",
            "*.tmp",
            "*.swp",
            "*~",
        ]

    # ANSI color codes
    GREEN = "\033[92m"
    RED = "\033[91m"
    YELLOW = "\033[93m"
    RESET = "\033[0m"

    def should_ignore(path: Path) -> bool:
        """Check if path matches any ignore pattern."""
        import os

        path_str = str(path)
        name = path.name

        for pattern in ignore_patterns:
            # Directory patterns (end with /)
            if pattern.endswith("/"):
                if pattern[:-1] in path_str.split(os.sep):
                    return True
            # Wildcard patterns
            elif "*" in pattern:
                if fnmatch.fnmatch(name, pattern):
                    return True
            # Exact match
            elif name == pattern:
                return True

        return False

    # Collect all files recursively
    files_to_upload = []
    for item in directory_path.rglob("*"):
        if item.is_dir():
            continue
        if should_ignore(item):
            continue

        # Calculate relative path from source directory
        rel_path = item.relative_to(directory_path)
        files_to_upload.append((item, str(rel_path)))

    if not files_to_upload:
        print("No files found to upload")
        return []

    print(f"Found {len(files_to_upload)} file(s) to upload")
    print()

    # Upload files
    results = []
    uploaded = 0
    failed = 0

    for file_path, rel_path in sorted(files_to_upload):
        # Determine target path
        rel_dir = str(Path(rel_path).parent)
        if rel_dir == ".":
            # Root file
            target_path = parent_path
        else:
            # File in subdirectory
            target_path = f"{parent_path}/{rel_dir}"

        try:
            result = upload_file(
                client=client,
                file_path=file_path,
                parent_path=target_path,
                owner=owner,
                rewrite=rewrite,
            )
            results.append(result)
            print(f"{GREEN}✓{RESET} {rel_path}")
            uploaded += 1
        except Exception as e:
            print(f"{RED}✗{RESET} {rel_path}: {e}")
            logger.error(f"Failed to upload {rel_path}: {e}")
            failed += 1

    if failed and not uploaded:
        raise RuntimeError(
            f"All {failed} file uploads to '{parent_path}' failed"
        )

    # Sync: Delete remote resources not present locally
    deleted = 0
    if sync:
        # Determine parent_id for collecting remote resources
        from .task_resources import (
            is_task_resource_path,
            parse_task_resource_path,
            resolve_task_resource_by_path,
            get_or_create_folder_in_task_resource,
        )

        if is_task_resource_path(parent_path):
            # TaskResource path
            catalog_path, task_name, internal_path = parse_task_resource_path(parent_path)
            task_id = resolve_task_resource_by_path(client, catalog_path, task_name)

            if internal_path:
                parent_id = get_or_create_folder_in_task_resource(client, task_id, internal_path)
            else:
                parent_id = task_id
        else:
            # Regular catalog path
            folder = get_or_create_folder_by_path(client=client, path=parent_path)
            parent_id = folder.resourceId

        # Collect all remote resources
        remote_resources = _collect_remote_resources(client, parent_id)

        # Build set of local paths (files + directories)
        local_paths = set()
        for _, rel_path in files_to_upload:
            local_paths.add(rel_path)
            # Also add parent directories
            parts = Path(rel_path).parts
            for i in range(1, len(parts)):
                dir_path = str(Path(*parts[:i]))
                local_paths.add(dir_path)

        # Delete remote resources not in local
        for rel_path, resource in sorted(remote_resources.items()):
            if rel_path not in local_paths:
                try:
                    client.catalog.delete_resource(resource.resourceId)
                    resource_type = (
                        "DIR" if resource.type == CatalogResourceType.DIRECTORY else "FILE"
                    )
                    print(f"{YELLOW}✗{RESET} {rel_path} [{resource_type}]")
                    deleted += 1
                except Exception as e:
                    print(f"{RED}✗{RESET} Failed to delete {rel_path}: {e}")
                    logger.error(f"Failed to delete {rel_path}: {e}")

    return results


def create_file(
    client: Client,
    name: str,
    content: Union[str, bytes],
    *,
    parent_path: Optional[str] = None,
    parent_id: Optional[str] = None,
    description: Optional[str] = None,
) -> CatalogResourceDc:
    """Create a new catalog file from in-memory content.

    Use this when the file body is built at runtime (rendered template,
    SQL output, etc.). For files already on disk use :func:`upload_file`.

    Either ``parent_path`` (catalog path, missing folders are created)
    or ``parent_id`` (resource ID) must be provided. ``content`` accepts
    ``str`` (UTF-8 encoded) or raw ``bytes``.

    Raises:
        ValueError: if ``parent_path`` and ``parent_id`` are both set or
            both missing.
        ResourceExists: if a file with this name already exists at the
            destination (use :func:`update_file` to overwrite it).
    """
    if parent_path is not None and parent_id is not None:
        raise ValueError("Pass either parent_path or parent_id, not both.")
    if parent_path is None and parent_id is None:
        raise ValueError("Pass parent_path or parent_id.")

    if parent_path is not None:
        parent_id = get_or_create_folder_by_path(client, parent_path).resourceId

    payload = content.encode("utf-8") if isinstance(content, str) else content

    try:
        return client.catalog.create_file_1(
            parentId=parent_id,
            fileName=name,
            file=payload,
            rewrite=False,
            description=description,
        )
    except Exception as e:
        raise_conflict_as_exists(e, resource=f"file {name!r}", parent_path=parent_path)
        raise


def download_file(
    client: Client,
    identifier: str,
    target_path: Union[str, Path],
    *,
    overwrite: bool = False,
) -> Path:
    """Download a catalog file's content to local disk.

    Wraps ``catalog.get_file`` (which returns ``bytes``) and writes the
    payload at ``target_path``.

    Args:
        client: An authenticated ``evergis_api.Client``.
        identifier: Catalog path, resource ID, or system name.
        target_path: Destination on disk. If it ends with ``/`` or
            already exists as a directory, the file is saved inside it
            under the resource's own name. Otherwise it is taken as the
            full destination file path. Missing parent directories are
            created automatically.
        overwrite: If the destination file already exists, replace it.
            Defaults to ``False`` (raises ``FileExistsError``).

    Returns:
        Absolute :class:`pathlib.Path` of the saved file.

    Raises:
        ValueError: if the resource cannot be resolved.
        FileExistsError: if ``target_path`` exists and ``overwrite`` is
            ``False``.
    """
    resource = resolve_resource(client, identifier)

    # Decide whether target_path is a directory (append resource.name)
    # or a full file path. ``is_dir()`` only catches an existing dir;
    # also treat trailing-separator paths as directories so the call
    # works on the first run before the dir is created.
    raw = str(target_path)
    target = Path(target_path)
    if target.is_dir() or raw.endswith(("/", "\\")):
        target = target / resource.name
        target.parent.mkdir(parents=True, exist_ok=True)
    else:
        target.parent.mkdir(parents=True, exist_ok=True)

    if target.exists() and not overwrite:
        raise FileExistsError(target)

    target.write_bytes(client.catalog.get_file(resourceId=resource.resourceId))
    return target.resolve()


def extract_zip(
    client: Client,
    archive: str,
    *,
    target_parent: Optional[str] = None,
    conflict_strategy: Union[str, ConflictResolutionStrategy] = "Skip",
    delete_zip_after: bool = False,
    extract_nested: bool = False,
) -> bool:
    """Extract a zip archive that already lives in the catalog.

    Wraps ``catalog.extract_zip_archive(ZipExtractRequestDc(...))``.

    Args:
        client: An authenticated ``evergis_api.Client``.
        archive: The zip resource - catalog path, resource ID, or
            system name.
        target_parent: Where to put the extracted entries. Catalog path
            (missing folders are created) or resource ID. Defaults to
            ``None``, which means "into the archive's own parent".
        conflict_strategy: How to handle name collisions inside the
            target. One of ``"Skip"`` (default), ``"Overwrite"``,
            ``"GenerateUnique"``, ``"ThrowError"``.
        delete_zip_after: Remove the source archive once the extraction
            completes.
        extract_nested: Also extract any zip archives found inside.

    Returns:
        ``True`` on success (the underlying endpoint returns a bool).
    """
    archive_id = resolve_resource(client, archive).resourceId

    target_id: Optional[str] = None
    if target_parent is not None:
        if ":" in target_parent:
            target_id = get_or_create_folder_by_path(
                client, target_parent
            ).resourceId
        else:
            target_id = resolve_resource(client, target_parent).resourceId

    return client.catalog.extract_zip_archive(
        body=ZipExtractRequestDc(
            resourceId=archive_id,
            targetParentId=target_id,
            conflictStrategy=conflict_strategy,
            deleteZipAfterExtraction=delete_zip_after,
            extractNestedArchives=extract_nested,
        )
    )


def update_file(
    client: Client,
    identifier: str,
    content: Union[str, bytes],
) -> CatalogResourceDc:
    """Overwrite an existing catalog file's content.

    Resolves ``identifier`` (path / id / system name) and rewrites the
    file body in place. The resulting resource keeps the same
    ``resourceId`` and ``parentId``; only ``size`` and the file
    contents change.

    .. note::
        The server's ``create_file`` endpoint matches the existing file
        by ``parentId + fileName`` when ``rewrite=True``. Passing only
        ``resourceId`` would create a brand-new file instead, so the
        wrapper resolves the parent and name first and uses those.

    .. note::
        Only the file content changes. To update ``description`` /
        ``tags`` / ``icon`` use :func:`update_resource_metadata`.

    Raises:
        ValueError: if the file cannot be resolved.
    """
    resource = resolve_resource(client, identifier)
    payload = content.encode("utf-8") if isinstance(content, str) else content

    return client.catalog.create_file_1(
        parentId=resource.parentId,
        fileName=resource.name,
        file=payload,
        rewrite=True,
    )
