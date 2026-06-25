"""Catalog management utilities for EverGIS."""

from .files import (
    create_file,
    download_file,
    extract_zip,
    update_file,
    upload_directory,
    upload_file,
    upload_files_by_extension,
)
from .folders import (
    create_folder,
    create_nested_folders,
    find_folder_by_name,
    get_or_create_folder,
    get_or_create_nested_folders,
    get_or_create_folder_by_path,
)
from .resources import (
    get_resources,
    iter_resources,
    iter_tags,
    resolve_resource,
    exists,
    delete_resource,
    rename_resource,
    update_resource_metadata,
    get_parents,
    create_link,
    resolve_parent_id,
    resolve_target_layer_parent,
    AccessMode,
    ResourceTypeFilter,
    CatalogResourceType,
    GeometryType,
    ResourceSubTypeFilter,
    PermissionLevel,
)
from .task_resources import (
    create_task_resource,
    is_task_resource_path,
    parse_task_resource_path,
    resolve_task_resource_by_path,
    create_folder_in_task_resource,
    get_or_create_folder_in_task_resource,
    upload_file_to_task_resource,
)
from .maps import (
    create_map,
    update_map,
    add_layer_to_map,
    remove_layer_from_map,
)
from .permissions import (
    get_permissions,
    set_permissions,
    add_permission,
    remove_permission,
)
from .data_sources import (
    create_data_source,
    update_data_source,
    test_data_source,
    get_data_source,
    delete_data_source,
    create_postgres_data_source,
    create_s3_data_source,
)

__all__ = [
    # File operations
    "upload_file",
    "upload_files_by_extension",
    "upload_directory",
    "create_file",
    "update_file",
    "download_file",
    "extract_zip",
    # Folder operations
    "create_folder",
    "create_nested_folders",
    "find_folder_by_name",
    "get_or_create_folder",
    "get_or_create_nested_folders",
    "get_or_create_folder_by_path",
    # Resource resolution
    "get_resources",
    "iter_resources",
    "iter_tags",
    "resolve_resource",
    "exists",
    "delete_resource",
    "rename_resource",
    "update_resource_metadata",
    "get_parents",
    "create_link",
    "resolve_parent_id",
    "resolve_target_layer_parent",
    # TaskResource operations
    "create_task_resource",
    "is_task_resource_path",
    "parse_task_resource_path",
    "resolve_task_resource_by_path",
    "create_folder_in_task_resource",
    "get_or_create_folder_in_task_resource",
    "upload_file_to_task_resource",
    # Types and enums
    "AccessMode",
    "ResourceTypeFilter",
    "CatalogResourceType",
    "GeometryType",
    "ResourceSubTypeFilter",
    "PermissionLevel",
    # Map operations
    "create_map",
    "update_map",
    "add_layer_to_map",
    "remove_layer_from_map",
    # Permission operations
    "get_permissions",
    "set_permissions",
    "add_permission",
    "remove_permission",
    # DataSource operations
    "create_data_source",
    "update_data_source",
    "test_data_source",
    "get_data_source",
    "delete_data_source",
    "create_postgres_data_source",
    "create_s3_data_source",
]
