"""Map (project) management utilities for EverGIS catalog."""

from __future__ import annotations

from typing import Any, List, Optional

from evergis_api import Client
from evergis_api.schemas import (
    ExtendedProjectInfoDc,
    ProjectConfigurationDc,
)

from .._errors import raise_conflict_as_exists
from .resources import resolve_resource


def create_map(
    client: Client,
    name: str,
    *,
    alias: Optional[str] = None,
    description: Optional[str] = None,
    parent_path: Optional[str] = None,
    tags: Optional[List[str]] = None,
    dashboard_configuration: Optional[Any] = None,
    edit_configuration: Optional[Any] = None,
) -> ExtendedProjectInfoDc:
    """Create a new map (project) in EverGIS.

    Args:
        client: EverGIS API client.
        name: Map system name (e.g., "username.my_map").
        alias: Display name for the map.
        description: Map description.
        parent_path: Catalog path for parent folder (e.g., "john_doe:Projects/Maps").
        tags: List of tags for the map.
        dashboard_configuration: Dashboard configuration (stored as-is).
        edit_configuration: Edit configuration (stored as-is).

    Returns:
        ExtendedProjectInfoDc: Created map info.

    Example:
        >>> from evergis_api import Client
        >>> from evergis_tools.catalog import create_map
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>> map_info = create_map(
        ...     client,
        ...     name="john_doe.my_map",
        ...     alias="My Map",
        ... )
        >>> print(f"Created map: {map_info.name}")
    """
    # Build configuration
    content = ProjectConfigurationDc(
        dashboardConfiguration=dashboard_configuration,
        editConfiguration=edit_configuration,
    )

    # Resolve parent ID if path provided
    parent_id: Optional[str] = None
    if parent_path:
        parent_resource = resolve_resource(client, parent_path)
        parent_id = parent_resource.resourceId

    # Build project info
    project = ExtendedProjectInfoDc(
        name=name,
        alias=alias,
        description=description,
        parentId=parent_id,
        tags=tags,
        content=content,
    )

    try:
        return client.projects.create_project(body=project)
    except Exception as e:
        raise_conflict_as_exists(
            e, resource=f"map {name!r}", alias=alias, parent_path=parent_path,
        )
        raise


def update_map(
    client: Client,
    name: str,
    *,
    alias: Optional[str] = None,
    description: Optional[str] = None,
    tags: Optional[List[str]] = None,
    dashboard_configuration: Optional[Any] = None,
    edit_configuration: Optional[Any] = None,
) -> ExtendedProjectInfoDc:
    """Update an existing map (project).

    Args:
        client: EverGIS API client.
        name: Map system name to update.
        alias: New display name (None to keep existing).
        description: New description (None to keep existing).
        tags: New tags (None to keep existing).
        dashboard_configuration: New dashboard configuration (None to keep existing).
        edit_configuration: New edit configuration (None to keep existing).

    Returns:
        ExtendedProjectInfoDc: Updated map info.

    Example:
        >>> update_map(client, "john_doe.my_map", alias="New Name")
    """
    # Get existing map
    existing = client.projects.get_project_info(name)
    content = existing.content or ProjectConfigurationDc()

    # Update alias if provided
    if alias is not None:
        existing.alias = alias

    # Update description if provided
    if description is not None:
        existing.description = description

    # Update tags if provided
    if tags is not None:
        existing.tags = tags

    # Update configurations if provided
    if dashboard_configuration is not None:
        content.dashboardConfiguration = dashboard_configuration
    if edit_configuration is not None:
        content.editConfiguration = edit_configuration

    existing.content = content

    # Drop server-managed timestamps from the patch payload. Setting
    # them to ``None`` is not enough because the generated client
    # serializes with ``exclude_unset=True`` - and Pydantic considers
    # a None assignment to be "set". Discarding from
    # ``__pydantic_fields_set__`` makes the serializer skip them.
    existing.__pydantic_fields_set__.discard("createdDate")
    existing.__pydantic_fields_set__.discard("changedDate")

    return client.projects.update_project(name=name, body=existing)


def add_layer_to_map(
    client: Client,
    map_name: str,
    layer_name: str,
    *,
    page_id: str = "page1",
    visible: bool = True,
    selectable: bool = True,
    parameters: Optional[dict] = None,
    prepend: bool = True,
) -> ExtendedProjectInfoDc:
    """Append a layer to a page in an existing map.

    Idempotent: if a layer with ``layer_name`` already exists on the
    target page nothing is added (the existing entry is left untouched
    and the function returns the unmodified map info).

    Args:
        client: EverGIS API client.
        map_name: Map system name (e.g. ``"john_doe.evg_map_features"``).
        layer_name: Full system name of the layer to append.
        page_id: Page id inside the dashboard's ``Pages`` container
            (default ``"page1"``). Use the value of ``id`` from the
            ``children`` of the ``templateName="Pages"`` node.
        visible: Initial visibility of the layer on the page.
        selectable: Whether features of the layer are selectable.
        parameters: Optional ``{"@param": "%filterName"}`` mapping for
            layers wired to a dashboard filter.
        prepend: ``True`` (default) puts the new layer at the top of the
            list - rendered above existing layers. ``False`` appends to
            the bottom.

    Returns:
        Updated ``ExtendedProjectInfoDc`` (or the unchanged one if the
        layer was already present).

    Raises:
        ValueError: if ``page_id`` is not found in the dashboard.
    """
    info = client.projects.get_project_info(map_name)
    cfg = info.content.dashboardConfiguration
    if not isinstance(cfg, dict):
        raise ValueError(
            f"map {map_name!r} has no dashboard configuration to update"
        )

    # Find the page. The dashboard is shaped as
    #   {"children": [ {templateName=Pages, "children": [pageN, ...]} ], ...}
    page = None
    for top in cfg.get("children", []):
        if top.get("templateName") == "Pages":
            for candidate in top.get("children", []):
                if candidate.get("id") == page_id:
                    page = candidate
                    break
            if page is not None:
                break
    if page is None:
        raise ValueError(
            f"page {page_id!r} not found in map {map_name!r}"
        )

    layers = page.setdefault("layers", [])
    # Idempotent: skip if the layer is already on the page.
    if any(lyr.get("name") == layer_name for lyr in layers):
        return info

    entry: dict = {
        "name": layer_name,
        "isVisible": visible,
        "selectable": selectable,
    }
    if parameters is not None:
        entry["parameters"] = parameters
    if prepend:
        layers.insert(0, entry)
    else:
        layers.append(entry)

    return update_map(
        client=client, name=map_name,
        dashboard_configuration=cfg,
    )


def remove_layer_from_map(
    client: Client,
    map_name: str,
    layer_name: str,
    *,
    page_id: str = "page1",
) -> ExtendedProjectInfoDc:
    """Remove a layer from a page in an existing map.

    Idempotent: if the layer is not on the page nothing changes.
    """
    info = client.projects.get_project_info(map_name)
    cfg = info.content.dashboardConfiguration
    if not isinstance(cfg, dict):
        return info

    page = None
    for top in cfg.get("children", []):
        if top.get("templateName") == "Pages":
            for candidate in top.get("children", []):
                if candidate.get("id") == page_id:
                    page = candidate
                    break
            if page is not None:
                break
    if page is None:
        return info

    before = page.get("layers") or []
    after = [lyr for lyr in before if lyr.get("name") != layer_name]
    if len(after) == len(before):
        return info
    page["layers"] = after
    return update_map(
        client=client, name=map_name,
        dashboard_configuration=cfg,
    )


__all__ = [
    "create_map",
    "update_map",
    "add_layer_to_map",
    "remove_layer_from_map",
]
