"""Resource management utilities for EverGIS catalog."""

from enum import Enum
from typing import Any, Iterator, Mapping, Optional, Sequence, Type, TypeVar, Union

from evergis_api import ApiClientError, Client
from evergis_api import schemas

from .._errors import ResourceNotFound, is_not_found, raise_conflict_as_exists
from .._http import silence_status_codes

# Re-export commonly used enums so callers do not depend on evergis_api.schemas directly.
AccessMode = schemas.AccessMode
ResourceTypeFilter = schemas.ResourceTypeFilter
CatalogResourceType = schemas.CatalogResourceType
GeometryType = schemas.OgcGeometryType
ResourceSubTypeFilter = schemas.ResourceSubTypeFilter
PermissionLevel = schemas.Permissions

__all__ = [
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
    "AccessMode",
    "ResourceTypeFilter",
    "CatalogResourceType",
    "GeometryType",
    "ResourceSubTypeFilter",
    "PermissionLevel",
]

EnumType = TypeVar("EnumType", bound=Enum)


def _is_resource_id(identifier: str) -> bool:
    """Check if identifier is a resource ID (UUID format without dashes)."""
    # Resource IDs are typically 32 hex characters without dashes
    # Example: efb02c4d89144f9792a94af22831f45d
    return len(identifier) == 32 and all(c in "0123456789abcdefABCDEF" for c in identifier)


def resolve_resource(
    client: Client,
    identifier: str,
    *,
    resource_type: Optional[Union[str, CatalogResourceType]] = None,
) -> schemas.CatalogResourceDc:
    """
    Universal function to resolve resource metadata from path, resource ID, or system name.

    Automatically detects the identifier type and uses the appropriate API method:
    1. Catalog path (contains '/' or ':') -> get_resource()
    2. Resource ID (32 hex chars) -> get_resource()
    3. System name (everything else) -> post_get_all(systemNames=[...])

    Since the v3 catalog update ``GET /resources/{resourceId}`` resolves
    both a 32-hex resource id and a catalog path (``owner/Folder/Name``),
    so the dedicated by-path / by-system-name endpoints are gone. The
    ``owner:rest`` form used across the examples is normalised to the
    server's ``owner/rest`` path form automatically.

    Args:
        client: Initialized EverGIS API client.
        identifier: Resource identifier - can be:
                    - Catalog path: "owner:Projects/Data/Layer" or "owner/Projects/Data/Layer"
                    - Resource ID: "efb02c4d89144f9792a94af22831f45d"
                    - System name: "skozhevanov.landplots_project"
        resource_type: When resolving by **system name**, a physical layer
            shares its systemName with the backing ``Table`` resource, so
            ``post_get_all`` returns BOTH (order is server-defined - Table
            often comes first). Pass ``"Layer"`` / ``"Table"`` / ``"Map"``
            etc. to pick the right one explicitly. Without it the first
            item is returned (legacy behaviour) - ambiguous for layers
            with a backing table. Ignored for path / resource-id lookups
            (those resolve a single resource already).

    Returns:
        CatalogResourceDc with full resource metadata (resourceId, systemName, type, etc.)

    Raises:
        ResourceNotFound: If the resource does not exist (404, or an empty
            result set for a system-name lookup).
        ValueError: For invalid input (non-str / empty identifier), a
            system name that resolves to no item of the requested
            ``resource_type``, or a resolved item without a resourceId.
        evergis_api.ApiClientError: Any other server-side failure (5xx,
            403, ...) propagates as-is - it is never masked as "not found".

    Examples:
        >>> from evergis_api import Client
        >>> from evergis_tools.catalog import resolve_resource
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>>
        >>> # Using catalog path
        >>> resource = resolve_resource(client, "owner:Projects/Data/Layer")
        >>> print(f"Resource ID: {resource.resourceId}")
        >>> print(f"System Name: {resource.systemName}")
        >>>
        >>> # Using resource ID
        >>> resource = resolve_resource(client, "efb02c4d89144f9792a94af22831f45d")
        >>>
        >>> # System name - disambiguate layer vs its backing table
        >>> layer = resolve_resource(client, "john_doe.my_layer", resource_type="Layer")
    """
    if not isinstance(identifier, str):
        raise ValueError(f"identifier must be str, got {type(identifier).__name__}")

    identifier = identifier.strip()

    if not identifier:
        raise ValueError("identifier cannot be empty")

    wanted_type = (
        resource_type.value
        if isinstance(resource_type, CatalogResourceType)
        else resource_type
    )

    resource_obj = None

    # 1. Catalog path: our "owner:rest" convention or the server's
    #    "owner/rest" form. Both resolve through GET /resources/{path}.
    if (":" in identifier or "/" in identifier) and not _is_resource_id(identifier):
        # Normalise "john_doe:Folder/Name" -> "john_doe/Folder/Name": the server's
        # path uses '/' throughout, including right after the owner.
        server_path = identifier.replace(":", "/", 1) if ":" in identifier else identifier
        # Percent-encode reserved characters ('&', '#', '?', ...) so they
        # reach the server intact; keep '/' as the path separator. httpx
        # passes the already-encoded value through without re-encoding.
        from urllib.parse import quote
        encoded = quote(server_path, safe="/")
        try:
            with silence_status_codes(404):
                resource_obj = client.catalog.get_resource(encoded)
        except ApiClientError as exc:
            if is_not_found(exc):
                raise ResourceNotFound(
                    f"Resource not found by path: '{identifier}'",
                    request=exc.request, response=exc.response,
                ) from None
            # Non-404 (5xx / 403 / ...) propagates as-is - it must not be
            # flattened into a ValueError that looks like "not found".
            raise

    # 2. Check if this is a resource ID (32 hex characters)
    elif _is_resource_id(identifier):
        try:
            with silence_status_codes(404):
                resource_obj = client.catalog.get_resource(identifier)
        except ApiClientError as exc:
            if is_not_found(exc):
                raise ResourceNotFound(
                    f"Resource not found by id: '{identifier}'",
                    request=exc.request, response=exc.response,
                ) from None
            raise

    # 3. Otherwise treat as system name
    else:
        try:
            with silence_status_codes(404):
                # limit must cover all resources sharing this systemName
                # (a physical layer + its backing Table) so the
                # resource_type filter can pick the right one.
                result = client.catalog.post_get_all(
                    body=schemas.ListResourcesDc(systemNames=[identifier]), limit=50
                )
            items = list(result.items or [])
            if not items:
                raise ResourceNotFound(
                    f"Resource not found by system name: '{identifier}'"
                )

            if wanted_type is not None:
                matches = [it for it in items if str(it.type) == wanted_type]
                if not matches:
                    present = sorted({str(it.type) for it in items})
                    raise ValueError(
                        f"No {wanted_type!r} resource with system name "
                        f"'{identifier}' (present: {present})"
                    )
                found_resource = matches[0]
            else:
                # Legacy: first item, order is server-defined.
                found_resource = items[0]

            if found_resource.resourceId:
                with silence_status_codes(404):
                    resource_obj = client.catalog.get_resource(found_resource.resourceId)
            else:
                raise ValueError(f"Resource with system name '{identifier}' has no resourceId")
        except (ValueError, ResourceNotFound):
            raise
        except ApiClientError as exc:
            if is_not_found(exc):
                raise ResourceNotFound(
                    f"Resource not found by system name: '{identifier}'",
                    request=exc.request, response=exc.response,
                ) from None
            raise

    return resource_obj


def create_link(
    client: Client,
    target: str,
    *,
    parent_path: Optional[str] = None,
    name: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[list] = None,
    log: bool = True,
) -> schemas.CatalogResourceDc:
    """Create a symlink (shortcut) to a resource.

    Args:
        client: EverGIS API client
        target: Target resource - catalog path, resource ID, or system name
            (resolved via resolve_resource)
        parent_path: Catalog path for the link location (auto-creates missing folders)
        name: Link display name (defaults to target resource name)
        description: Link description
        tags: List of tags
        log: Enable logging

    Returns:
        CatalogResourceDc for the created link

    Raises:
        ResourceNotFound: If target cannot be resolved.
        ResourceExists: If a link with this name already exists in the folder.

    Example:
        >>> from evergis_tools.catalog import create_link
        >>> link = create_link(client, "john_doe.realty", parent_path="john_doe:Projects/Links")
    """
    import logging
    logger = logging.getLogger(__name__)

    # Resolve target resource
    resource = resolve_resource(client, target)
    target_id = resource.resourceId

    if log:
        logger.info(f"Creating link to '{target}' (resourceId: {target_id})")

    # Resolve parent folder
    parent_id = None
    if parent_path is not None:
        from .folders import get_or_create_folder_by_path
        folder = get_or_create_folder_by_path(client, parent_path)
        parent_id = folder.resourceId
        if log:
            logger.info(f"Link parent folder: {parent_path} (ID: {parent_id})")

    # Default name from resource
    link_name = name or getattr(resource, "systemName", None) or target

    body = schemas.CreateSymlinkDc(
        name=link_name,
        targetResourceId=target_id,
        parentId=parent_id,
        description=description,
        tags=tags,
    )

    try:
        result = client.catalog.post_link(body=body)
    except Exception as e:
        raise_conflict_as_exists(e, resource=f"link {link_name!r}", parent_path=parent_path)
        raise

    if log:
        logger.info(f"Created link '{link_name}' -> '{target}' (ID: {result.resourceId})")

    return result


def _normalize_enum_value(
    value: Optional[Union[str, EnumType]],
    enum_cls: Type[EnumType],
    param_name: str,
) -> Optional[EnumType]:
    if value is None:
        return None
    if isinstance(value, enum_cls):
        return value
    try:
        return enum_cls(value)
    except ValueError as exc:
        raise ValueError(f"Invalid value '{value}' for parameter '{param_name}'.") from exc


def _normalize_enum_sequence(
    values: Optional[Sequence[Union[str, EnumType]]],
    enum_cls: Type[EnumType],
    param_name: str,
) -> Optional[list[EnumType]]:
    if values is None:
        return None
    normalized: list[EnumType] = []
    for item in values:
        converted = _normalize_enum_value(item, enum_cls, param_name)
        if converted is None:
            raise ValueError(f"Parameter '{param_name}' does not accept empty values.")
        normalized.append(converted)
    return normalized


def get_resources(
    client: Client,
    filter_text: Optional[str] = None,
    owner_filter: Optional[Union[str, AccessMode]] = None,
    resource_types: Optional[Sequence[Union[str, ResourceTypeFilter]]] = None,
    catalog_resource_types: Optional[Sequence[Union[str, CatalogResourceType]]] = None,
    geometry_types: Optional[Sequence[Union[str, GeometryType]]] = None,
    parent: Optional[str] = None,
    subtypes: Optional[Sequence[Union[str, ResourceSubTypeFilter]]] = None,
    system_names: Optional[Sequence[str]] = None,
    acl_filter: Optional[Mapping[str, Union[str, PermissionLevel]]] = None,
    limit: Optional[int] = 100,
    offset: Optional[int] = None,
    order_by: Optional[Sequence[str]] = None,
    tags_filter: Optional[Union[schemas.TagsFilterDc, Mapping[str, Any]]] = None,
) -> schemas.PagedResourcesListDc:
    """Get list of resources from EverGIS catalog.

    Args:
        client: Initialized EverGIS API client.
        filter_text: Text filter with wildcard support (`*`).
        owner_filter: Owner restriction. Valid values: 'My', 'Shared', 'Public'.
        resource_types: Resource types. Valid values: 'Map', 'Layer', 'Table', 'RasterCatalog',
            'ProxyService', 'RemoteTileService', 'File', 'DataSource', 'TaskPrototype'.
        catalog_resource_types: Catalog item types. Valid values: 'Directory', 'Map', 'Layer',
            'Table', 'File', 'TaskPrototype', 'DataSource'.
        geometry_types: Geometry type filter. Valid values: 'Point', 'Geometry', 'Polyline',
            'MultiPolygon', 'Polygon', 'Multipoint', etc. (see GeometryType).
        parent: Parent resource identifier (str) or catalog path (str).
                Resource ID: "4d2457f6568145f5af3a42ba73d48d79"
                Path: "owner:Projects/Data"
        subtypes: Resource subtypes. Valid values: 'RemoteTileService', 'ProxyService', 'QueryLayerService',
            'TileCatalogTable'.
        system_names: List of system names for filtering.
        acl_filter: Role and permission restrictions. Permission values are specified as strings
            (e.g., 'read', 'write', 'read,write').
        limit: Result page size.
        offset: Offset from beginning of results.
        order_by: Sorting fields.
        tags_filter: Tag filter (`schemas.TagsFilterDc`).

    Returns:
        Paged list of resources.

    Raises:
        ValueError: If parameters are invalid.

    Examples:
        >>> from evergis_api import Client
        >>> from evergis_tools.catalog import get_resources
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>>
        >>> # Get resources with filters
        >>> resources = get_resources(
        ...     client,
        ...     filter_text="my_layer*",
        ...     owner_filter="My",
        ...     resource_types=["Layer"]
        ... )
        >>> print(f"Found {resources.totalCount} resources")
        >>>
        >>> # Get resources from specific parent using path
        >>> resources = get_resources(
        ...     client,
        ...     parent="owner:Projects/Data",
        ...     catalog_resource_types=["Layer"]
        ... )
        >>>
        >>> # Get resources from specific parent using ID
        >>> resources = get_resources(
        ...     client,
        ...     parent="4d2457f6568145f5af3a42ba73d48d79",
        ...     catalog_resource_types=["Layer"]
        ... )
    """

    for param_name, value in ("limit", limit), ("offset", offset):
        if value is not None and value < 0:
            raise ValueError(f"Parameter '{param_name}' must be non-negative.")

    # Resolve parent to resource ID if provided
    parent_id = None
    if parent is not None:
        resource_obj = resolve_resource(client, parent)
        parent_id = resource_obj.resourceId

    owner_mode = _normalize_enum_value(owner_filter, AccessMode, "owner_filter")
    types = _normalize_enum_sequence(resource_types, ResourceTypeFilter, "resource_types")
    catalog_types = _normalize_enum_sequence(
        catalog_resource_types,
        CatalogResourceType,
        "catalog_resource_types",
    )
    geometry = _normalize_enum_sequence(
        geometry_types,
        GeometryType,
        "geometry_types",
    )
    subtype_filters = _normalize_enum_sequence(
        subtypes,
        ResourceSubTypeFilter,
        "subtypes",
    )

    acl_filter_payload = None
    if acl_filter:
        acl_filter_payload = {}
        for role, permission in acl_filter.items():
            converted = _normalize_enum_value(permission, PermissionLevel, "acl_filter")
            if converted is None:
                raise ValueError("Parameter 'acl_filter' requires permission values.")
            acl_filter_payload[role] = converted

    tags_filter_dc = None
    if tags_filter is not None:
        if isinstance(tags_filter, schemas.TagsFilterDc):
            tags_filter_dc = tags_filter
        else:
            tags_filter_dc = schemas.TagsFilterDc.model_validate(dict(tags_filter))
            
    resource_request = schemas.ListResourcesDc(
        filter=filter_text,
        ownerFilter=owner_mode,
        types=types,
        resourceTypes=catalog_types,
        geometryTypes=geometry,
        parentId=parent_id,
        subtypes=subtype_filters,
        systemNames=list(system_names) if system_names is not None else None,
        orderBy=list(order_by) if order_by is not None else None,
        tagsFilter=tags_filter_dc,
        aclFilter=acl_filter_payload,
    )
    
    return client.catalog.post_get_all(
        body=resource_request,
        limit=limit,
        offset=offset,
    )


def resolve_target_layer_parent(
    client: Client,
    target_layer: str,
    target_layer_parent_path: Optional[str] = None,
) -> Optional[str]:
    """Resolve parent folder ID for target layer.

    If target layer already exists, returns its existing parent ID and prints a message.
    If target layer doesn't exist and parent_path is provided, creates missing folders
    and returns the folder resource ID.

    This function is useful for tasks that create or update layers, allowing them to:
    - Reuse existing layer locations without specifying parent path
    - Automatically create folder hierarchies when needed
    - Avoid unnecessary folder creation

    Args:
        client: Initialized EverGIS API client.
        target_layer: Target layer name/identifier (system name, resource ID, or catalog path).
        target_layer_parent_path: Optional catalog path for parent folder (e.g., "john_doe:Projects/Data").
                                  Only used if layer doesn't exist.

    Returns:
        Parent folder resource ID or None if layer doesn't exist and no path provided.

    Examples:
        >>> from evergis_api import Client
        >>> from evergis_tools.catalog import resolve_target_layer_parent
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>>
        >>> # Layer exists - uses its current parent
        >>> parent_id = resolve_target_layer_parent(
        ...     client=client,
        ...     target_layer="john_doe.existing_layer",
        ...     target_layer_parent_path="john_doe:Projects/NewFolder"  # Ignored
        ... )
        Layer 'john_doe.existing_layer' already exists, using existing parent folder
        >>>
        >>> # Layer doesn't exist - creates folders and returns parent ID
        >>> parent_id = resolve_target_layer_parent(
        ...     client=client,
        ...     target_layer="john_doe.new_layer",
        ...     target_layer_parent_path="john_doe:Projects/NewFolder"  # Created if needed
        ... )
    """
    from .folders import get_or_create_folder_by_path

    # Check if target layer already exists
    try:
        existing_layer = resolve_resource(client=client, identifier=target_layer)
        if existing_layer.type == "Layer":
            print(f"Layer '{target_layer}' already exists, using existing parent folder")
            return existing_layer.parentId
        else:
            # If exists but not a Layer, create in specified path
            if target_layer_parent_path is not None:
                folder = get_or_create_folder_by_path(client=client, path=target_layer_parent_path)
                return folder.resourceId
            return None
    except ResourceNotFound:
        # Only "not found" means "fall through to create the folder". Real
        # API errors (5xx / 403) propagate from inside ``resolve_resource``.
        if target_layer_parent_path is not None:
            folder = get_or_create_folder_by_path(client=client, path=target_layer_parent_path)
            return folder.resourceId
        return None


def resolve_parent_id(
    client: Client,
    parent_id: Optional[str] = None,
    parent_path: Optional[str] = None,
) -> str:
    """Resolve parent folder ID from either parent_id or parent_path.

    This is a utility function to eliminate code duplication in functions
    that accept both parent_id and parent_path parameters.

    Args:
        client: EverGIS API client
        parent_id: Direct parent folder resource ID. Mutually exclusive with parent_path.
        parent_path: Catalog path to parent folder (e.g., "john_doe:Projects/Folder").
            If the path doesn't exist, all missing folders will be created automatically.
            Mutually exclusive with parent_id.

    Returns:
        Resolved parent folder resource ID.

    Raises:
        ValueError: If both parent_id and parent_path are provided, or neither is provided.

    Examples:
        >>> # Using parent_id directly
        >>> folder_id = resolve_parent_id(client, parent_id="abc123...")
        >>>
        >>> # Using parent_path (creates folders if needed)
        >>> folder_id = resolve_parent_id(client, parent_path="john_doe:Projects/New")
    """
    from .folders import get_or_create_folder_by_path

    if parent_id is not None and parent_path is not None:
        raise ValueError("Cannot specify both parent_id and parent_path")
    if parent_id is None and parent_path is None:
        raise ValueError("Must specify either parent_id or parent_path")

    if parent_id is not None:
        return parent_id

    parent_folder = get_or_create_folder_by_path(client, parent_path)
    return parent_folder.resourceId


def exists(client: Client, identifier: str) -> bool:
    """Check whether a resource exists in the catalog.

    Resolution strategy by identifier shape:

    * 32-char hex resource ID or catalog path -> ``resource_exists_by_id_async``
      (``GET /resources/exists/{id}``). Despite the name this endpoint accepts
      a v3 catalog path (``owner/Folder/Name``) just as well as a 32-hex id,
      for any resource type (folder, layer, map, task resource, ...). It
      returns a plain ``bool`` - cheaper than a full resolve and no 404 to
      catch;
    * system name (dotted, e.g. ``john_doe.my_layer``) -> ``resolve_resource`` and
      treat "not found" as ``False``. The exists endpoint does not understand
      system names (it reads them as a path), so the listing-based resolve is
      still needed here.

    Returns ``True`` only for genuine existence; generic API errors
    (auth, 5xx) still propagate.

    Args:
        client: An authenticated ``evergis_api.Client``.
        identifier: Catalog path, resource ID, or system name.

    Returns:
        ``True`` if the resource exists.
    """
    if not isinstance(identifier, str):
        raise ValueError(
            f"identifier must be str, got {type(identifier).__name__}"
        )
    identifier = identifier.strip()
    if not identifier:
        raise ValueError("identifier cannot be empty")

    # A 32-hex id, or a catalog path (contains ':' or '/'): both go through
    # the dedicated bool endpoint. Normalise the legacy 'owner:rest' form to
    # 'owner/rest' and percent-encode reserved characters (keeping '/').
    if _is_resource_id(identifier):
        probe = identifier
    elif ":" in identifier or "/" in identifier:
        from urllib.parse import quote
        server_path = identifier.replace(":", "/", 1) if ":" in identifier else identifier
        probe = quote(server_path, safe="/")
    else:
        probe = None

    if probe is not None:
        # The endpoint returns False for an absent resource, but a stale
        # server can still 404 - swallow that into a plain bool.
        try:
            with silence_status_codes(404):
                return client.catalog.resource_exists_by_id_async(resourceId=probe)
        except ApiClientError as exc:
            if is_not_found(exc):
                return False
            raise

    # System name (dotted): no exists endpoint understands it - resolve and
    # treat ResourceNotFound as False (5xx / 403 still propagate).
    try:
        resolve_resource(client, identifier)
        return True
    except ResourceNotFound:
        return False


def delete_resource(
    client: Client,
    identifier: str,
    *,
    cascade: bool = True,
    missing_ok: bool = False,
    resource_type: Optional[Union[str, CatalogResourceType]] = None,
) -> bool:
    """Delete a catalog resource by id, path, or system name.

    Resolves the identifier first, then issues
    ``catalog.delete_resource(cascade=True)``. ``cascade=True`` is the
    default - it makes sure the backing table of a layer is dropped along
    with the layer itself (without it the orphan table survives and the
    next create fails with "table already exist").

    Args:
        client: An authenticated ``evergis_api.Client``.
        identifier: Catalog path, resource ID, or system name.
        cascade: Cascade-delete dependent resources (default ``True``).
        missing_ok: If ``True``, return ``False`` instead of raising
            when the resource does not exist.

    Returns:
        ``True`` if the resource was deleted, ``False`` if missing and
        ``missing_ok=True``.

    Raises:
        ResourceNotFound: if the resource is not found and ``missing_ok=False``.
        evergis_api.ApiClientError: on any server-side failure during
            the delete itself.
    """
    try:
        resource = resolve_resource(client, identifier, resource_type=resource_type)
    except ResourceNotFound:
        if missing_ok:
            return False
        raise
    # The server's ``delete_resource`` returns False even on successful
    # deletion - normalize: any non-error return means it worked.
    client.catalog.delete_resource(
        resourceId=resource.resourceId, cascade=cascade
    )
    return True


def iter_resources(
    client: Client,
    *,
    filter_text: Optional[str] = None,
    owner_filter: Union[str, AccessMode] = "My",
    resource_types: Optional[Sequence[Union[str, ResourceTypeFilter]]] = None,
    catalog_resource_types: Optional[
        Sequence[Union[str, CatalogResourceType]]
    ] = None,
    geometry_types: Optional[Sequence[Union[str, GeometryType]]] = None,
    parent: Optional[str] = None,
    subtypes: Optional[Sequence[Union[str, ResourceSubTypeFilter]]] = None,
    system_names: Optional[Sequence[str]] = None,
    acl_filter: Optional[Mapping[str, Union[str, PermissionLevel]]] = None,
    order_by: Optional[Sequence[str]] = None,
    tags_filter: Optional[
        Union[schemas.TagsFilterDc, Mapping[str, Any]]
    ] = None,
    page_size: int = 1000,
) -> Iterator[schemas.CatalogResourceDc]:
    """Stream every resource matching the filters, paging through the API.

    The server caps each ``post_get_all`` response - this generator
    automatically fetches subsequent pages until there are no more.
    Same filtering options as :func:`get_resources`; use that one when
    a single page is enough.

    Args:
        owner_filter: Owner scope. The server rejects null - one of
            ``"My"`` (default; current user's own resources),
            ``"Shared"`` (resources others shared with the user), or
            ``"Public"`` (publicly visible resources).
        See :func:`get_resources` for the rest of the per-filter semantics.
        page_size: Items per request (default 1000).

    Yields:
        ``CatalogResourceDc`` instances.
    """
    offset = 0
    while True:
        page = get_resources(
            client,
            filter_text=filter_text,
            owner_filter=owner_filter,
            resource_types=resource_types,
            catalog_resource_types=catalog_resource_types,
            geometry_types=geometry_types,
            parent=parent,
            subtypes=subtypes,
            system_names=system_names,
            acl_filter=acl_filter,
            limit=page_size,
            offset=offset,
            order_by=order_by,
            tags_filter=tags_filter,
        )
        items = list(page.items or [])
        for r in items:
            yield r
        if len(items) < page_size:
            return
        offset += page_size


def rename_resource(
    client: Client,
    identifier: str,
    *,
    new_name: Optional[str] = None,
    new_parent: Optional[str] = None,
    rewrite: bool = False,
) -> schemas.CatalogResourceDc:
    """Rename and/or move a resource.

    Picks the right server endpoint depending on the arguments:

    * ``new_name`` only -> ``catalog.patch_resource(name=...)`` (in-place
      rename).
    * ``new_parent`` set (with or without ``new_name``) ->
      ``catalog.move_resource(MoveResourceDc(...))``.

    At least one of ``new_name`` or ``new_parent`` must be provided.

    Args:
        client: An authenticated ``evergis_api.Client``.
        identifier: Resource to rename - catalog path, resource ID, or
            system name.
        new_name: New display name for the resource.
        new_parent: New parent location - catalog path or resource ID.
            Missing folders along the path are created automatically.
        rewrite: If a resource with the new name already exists at the
            target, overwrite it. Defaults to ``False`` (server raises).
            Only honored on the move path.

    Returns:
        Updated ``CatalogResourceDc``.

    Raises:
        ValueError: if both ``new_name`` and ``new_parent`` are ``None``,
            or if the source / target cannot be resolved.
    """
    if new_name is None and new_parent is None:
        raise ValueError(
            "Pass at least one of new_name or new_parent."
        )

    resource = resolve_resource(client, identifier)

    target_resource_id: Optional[str] = None
    if new_parent is not None:
        from .folders import get_or_create_folder_by_path
        if ":" in new_parent:
            target_resource_id = get_or_create_folder_by_path(
                client, new_parent
            ).resourceId
        else:
            target_resource_id = resolve_resource(client, new_parent).resourceId

    # The server has two endpoints with overlapping but limited
    # responsibilities:
    #
    # * move_resource(targetResource=...)      - changes parent only.
    #   Throws 409 if the target equals the current parent. The
    #   ``newName`` field on the body is silently ignored.
    # * patch_resource(name=..., ...)          - renames in place.
    #   Cannot move; clears any metadata field omitted from the body.
    #
    # We orchestrate both: do the move first when the parent really
    # changes, then patch for rename if requested.
    needs_move = (
        target_resource_id is not None
        and target_resource_id != resource.parentId
    )

    if needs_move:
        client.catalog.move_resource(
            resourceId=resource.resourceId,
            body=schemas.MoveResourceDc(
                targetResource=target_resource_id,
                rewrite=rewrite,
            ),
        )
        if new_name is None:
            return resolve_resource(client, resource.resourceId)

    # Rename in place (after a possible move). Carry existing
    # description / tags / icon along, otherwise the server clears them.
    fresh = resolve_resource(client, resource.resourceId)
    return client.catalog.patch_resource(
        resourceId=fresh.resourceId,
        body=schemas.PatchResourceDc(
            name=new_name if new_name is not None else fresh.name,
            description=fresh.description,
            tags=list(fresh.tags) if fresh.tags else None,
            icon=fresh.icon,
        ),
    )


def iter_tags(
    client: Client,
    *,
    filter: Optional[str] = None,
    page_size: int = 1000,
) -> Iterator[str]:
    """Stream every tag the user can see, paging through the API.

    Useful for tag-autocomplete UI or for inventorying which tags are
    in use across the user's catalog.

    Args:
        client: An authenticated ``evergis_api.Client``.
        filter: Optional substring filter applied server-side.
        page_size: Items per request (default 1000).

    Yields:
        Tag strings.
    """
    offset = 0
    while True:
        page = client.catalog.get_tags(
            filter=filter, limit=page_size, offset=offset
        )
        items = list(page.items or [])
        for tag in items:
            yield tag
        if len(items) < page_size:
            return
        offset += page_size


def get_parents(
    client: Client,
    identifier: str,
) -> list[schemas.ResourceParentDc]:
    """Return the chain of ancestor folders for a resource.

    Useful for building breadcrumb UI or printing the catalog path of
    a resource you only have a system name / id for. The list is
    ordered from the catalog root down to the immediate parent
    (the resource itself is not included).

    Args:
        client: An authenticated ``evergis_api.Client``.
        identifier: Catalog path, resource ID, or system name.

    Returns:
        List of ``ResourceParentDc`` (``name``, ``path``, ``resourceId``)
        from root to immediate parent. Empty list if the resource
        sits at the root.
    """
    resource = resolve_resource(client, identifier)
    return list(client.catalog.get_parents(resourceId=resource.resourceId))


def update_resource_metadata(
    client: Client,
    identifier: str,
    *,
    description: Optional[str] = None,
    tags: Optional[Sequence[str]] = None,
    icon: Optional[str] = None,
) -> schemas.CatalogResourceDc:
    """Patch a resource's metadata (description / tags / icon).

    Wraps ``catalog.patch_resource(PatchResourceDc(...))``. The server
    clears any field omitted from the body, so the helper reads the
    current resource and only overrides the fields you pass; everything
    else is preserved.

    For renaming a resource use :func:`rename_resource`.

    Args:
        client: An authenticated ``evergis_api.Client``.
        identifier: Resource to update - catalog path, resource ID, or
            system name.
        description: New description. ``None`` keeps the existing one;
            pass ``""`` to clear.
        tags: New tag list. ``None`` keeps the existing tags;
            pass ``[]`` to clear.
        icon: New icon URI / id. ``None`` keeps the existing one;
            pass ``""`` to clear.

    Returns:
        Updated ``CatalogResourceDc``.
    """
    resource = resolve_resource(client, identifier)
    return client.catalog.patch_resource(
        resourceId=resource.resourceId,
        body=schemas.PatchResourceDc(
            name=resource.name,
            description=(
                description if description is not None else resource.description
            ),
            tags=(
                list(tags)
                if tags is not None
                else (list(resource.tags) if resource.tags else None)
            ),
            icon=icon if icon is not None else resource.icon,
        ),
    )
