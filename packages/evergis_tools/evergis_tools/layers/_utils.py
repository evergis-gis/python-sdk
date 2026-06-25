# -*- coding: utf-8 -*-
"""Internal utilities for layer operations."""

from typing import Optional, Any, Union, Literal, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    import geopandas as gpd

from evergis_api import Client
from evergis_api.schemas import (
    AttributesConfigurationDc,
    AttributeConfigurationDc,
    AttributeType,
    ListResourcesDc,
    QueryLayerServiceEqlParameterConfigurationDc,
)
from evergis_api._generated.exceptions import ApiClientError

from .._errors import ResourceExists, is_not_found
from .._http import silence_status_codes
from .._utils import to_safe_field_name
from ..attributes import _pandas_dtype_to_attribute_type, _get_geometry_attribute_type

logger = logging.getLogger(__name__)

# Type alias for overwrite parameter
OverwriteMode = Union[bool, Literal["cascade"]]


def _handle_layer_overwrite(
    client: Client,
    layer_name: str,
    create_table: bool = False,
    overwrite: OverwriteMode = False,
    check_dependencies: bool = False,
    strict_errors: bool = False,
    log: bool = True,
) -> list:
    """Handle overwrite logic for layer creation functions.

    Provides unified logic for checking existence and deleting existing layers/tables
    before creating new ones. Supports dependency deletion for query layers.

    Args:
        client: EverGIS API client
        layer_name: Full layer name (with username prefix)
        create_table: Whether a table will be created (checks table existence)
        overwrite: Controls overwrite behavior:
            - False: raise error if resources exist
            - True / "cascade": delete the existing layer with cascade=True
        check_dependencies: If True, query and delete dependent resources (for query layers)
        strict_errors: If True, raise RuntimeError on deletion failure; if False, log warnings
        log: Enable logging

    Returns:
        List of deletion responses

    Raises:
        ValueError: When resource exists and overwrite=False
        RuntimeError: When deletion fails and strict_errors=True

    Note:
        Deleting the layer with ``cascade=True`` is enough - the
        backing table is a child of the layer and EverGIS removes it
        automatically. We don't issue a separate ``delete`` for the
        ``.table`` resource (verified: drop layer → table gone too).
    """
    from ..catalog import delete_resource as _delete_resource_by_identifier

    response = []

    # One catalog query resolves both the layer and its backing table:
    # they share a systemName, so post_get_all returns both rows and we
    # split them by type. A ``.table`` present without its parent layer is
    # detected so overwrite=False can raise a clear error here instead of
    # the create failing later with "table already exist".
    layer_item = None
    table_exists = False
    try:
        with silence_status_codes(404):
            siblings = client.catalog.post_get_all(
                body=ListResourcesDc(systemNames=[layer_name]), limit=50
            )
        for item in (siblings.items or []):
            if str(item.type) == "Layer":
                layer_item = item
            elif str(item.type) == "Table" and create_table:
                table_exists = True
    except ApiClientError as e:
        if not is_not_found(e):
            raise
    layer_exists = layer_item is not None

    # If overwrite=False, raise error if resources exist
    if not overwrite:
        if layer_exists:
            raise ResourceExists(
                f"Layer '{layer_name}' already exists. Use overwrite=True to overwrite"
            )
        if table_exists:
            raise ResourceExists(
                f"Table '{layer_name}' already exists. Use overwrite=True to overwrite"
            )
        return response

    # overwrite=True or "cascade": delete the layer with cascade=True.
    # The backing table goes with it - no separate table delete.
    deletion_errors = []

    # Handle dependencies if requested (for query layers).
    if check_dependencies and layer_exists:
        try:
            # GET /layers/{name}/dependencies -> ResourceDependenciesDc;
            # `name` is the layer's system name, and the payload carries
            # a `.dependencies` list of DependentResourceDc (name + type).
            deps = client.layers.get_resource_dependencies(name=layer_name)
            dep_list = getattr(deps, "dependencies", None) or []
            if log and dep_list:
                logger.info(f"Found {len(dep_list)} dependent resources to delete")
            for dep in dep_list:
                dep_name = getattr(dep, "name", None)
                if not dep_name:
                    continue
                try:
                    if log:
                        logger.info(f"Deleting dependent resource: {dep_name}")
                    # resolve the dependent's system name to an id, then drop
                    _delete_resource_by_identifier(
                        client, dep_name, cascade=True, missing_ok=True
                    )
                except Exception as e:
                    error_msg = f"Could not delete dependent resource {dep_name}: {e}"
                    if strict_errors:
                        deletion_errors.append(error_msg)
                    if log:
                        logger.warning(error_msg)
        except Exception as e:
            error_msg = f"Could not get/delete dependencies: {e}"
            if strict_errors:
                deletion_errors.append(error_msg)
            if log:
                logger.warning(error_msg)

    # Delete the layer (cascade=True takes the backing table with it).
    if layer_exists:
        try:
            if log:
                logger.info(f"Deleting existing layer '{layer_name}' (id={layer_item.resourceId})")
            response.append(
                client.catalog.delete_resource(layer_item.resourceId, cascade=True)
            )
        except Exception as e:
            # A 404 means the layer is already gone - safe to proceed to
            # create. Any other failure means the delete did NOT happen, so
            # creating now would collide with a confusing "table already
            # exist". Stop loudly instead of silently warning and continuing.
            if is_not_found(e):
                if log:
                    logger.debug(f"Layer '{layer_name}' already absent before delete")
            else:
                raise RuntimeError(
                    f"Failed to delete existing layer '{layer_name}' before overwrite; "
                    f"creation cancelled. Original error: {e}"
                ) from e

    # Handle deletion errors based on strict_errors flag
    if deletion_errors and strict_errors:
        raise RuntimeError(
            f"Failed to delete existing resources for '{layer_name}'. Creation cancelled.\n"
            + "\n".join(deletion_errors)
        )

    return response


def _convert_geometry_type(
    geometry_type: Any, log: bool = True, fallback: Optional[Any] = None
) -> Optional[Any]:
    """Convert geometry type from various formats to AttributeType enum.

    Helper function to standardize geometry type conversion across layer creation functions.
    Accepts geometry type as string, AttributeType enum, or None, and converts to AttributeType.

    Args:
        geometry_type: Geometry type in any format:
            - String: "Point", "Polygon", "MultiPolygon", etc. (case-insensitive)
            - AttributeType enum: AttributeType.POINT, AttributeType.POLYGON, etc.
            - None: Returns fallback or None
        log: Enable logging for warnings (default True)
        fallback: Value to return if conversion fails (default None)

    Returns:
        AttributeType enum value, fallback value, or None

    Example:
        >>> _convert_geometry_type("Polygon")
        <AttributeType.POLYGON: 'Polygon'>
        >>> _convert_geometry_type("multipolygon")
        <AttributeType.MULTI_POLYGON: 'MultiPolygon'>
        >>> _convert_geometry_type(AttributeType.POINT)
        <AttributeType.POINT: 'Point'>
        >>> _convert_geometry_type("InvalidType", fallback=AttributeType.POINT)
        <AttributeType.POINT: 'Point'>
    """
    # If None, return fallback
    if geometry_type is None:
        return fallback

    # If already AttributeType enum, return as-is
    if hasattr(geometry_type, "__class__") and geometry_type.__class__.__name__ == "AttributeType":
        return geometry_type

    # Try to convert string to AttributeType enum
    if isinstance(geometry_type, str):
        try:
            # Try uppercase first (e.g., "Point" -> "POINT" -> AttributeType.POINT)
            geom_type_attr = getattr(AttributeType, geometry_type.upper(), None)

            if geom_type_attr is None:
                # Try as-is (e.g., "Polygon" -> AttributeType("Polygon"))
                geom_type_attr = AttributeType(geometry_type)

            return geom_type_attr

        except (ValueError, AttributeError):
            if log:
                logger.warning(
                    f"Invalid geometry type: '{geometry_type}'. "
                    f"Supported types: Point, LineString, Polygon, MultiPolygon, etc. "
                    f"{'Using fallback.' if fallback else 'Returning None.'}"
                )
            return fallback

    # Unknown type, return fallback
    if log:
        logger.warning(
            f"Unexpected geometry_type format: {type(geometry_type)}. "
            f"Expected string or AttributeType enum. "
            f"{'Using fallback.' if fallback else 'Returning None.'}"
        )
    return fallback


def _infer_attribute_type(value: Any) -> AttributeType:
    """Infer AttributeType from Python value."""
    if isinstance(value, bool):
        return AttributeType.BOOLEAN
    elif isinstance(value, int):
        return AttributeType.INT64
    elif isinstance(value, float):
        return AttributeType.DOUBLE
    elif isinstance(value, list):
        if value:
            return _infer_attribute_type(value[0])
        return AttributeType.STRING
    return AttributeType.STRING


def declare_eql_parameter(
    type_name: str,
    *,
    default: Any = None,
    alias: str = "",
    description: str = "",
    is_array: bool = False,
) -> QueryLayerServiceEqlParameterConfigurationDc:
    """Build an EQL parameter declaration for a layer config.

    Two patterns:

    * ``declare_eql_parameter("String")`` - declaration WITHOUT a
      triggering default. ``default`` becomes ``""`` for ``String`` and
      ``None`` for everything else - the value the server treats as
      "not set", so a matching ``${isset:@x, {...}}`` expansion in the
      layer's EQL does NOT inject a filter when the client omits the
      parameter.
    * ``declare_eql_parameter("String", default="TEST")`` - declaration
      WITH a default. The server uses ``"TEST"`` whenever the client
      omits the parameter, so the layer behaves as if ``@x = "TEST"``
      is always present (until the client overrides it).

    Args:
        type_name: AttributeType name - "String", "Double", "Int64",
            "Boolean", "DateTime".
        default: Optional default value. If ``None`` and
            ``type_name == "String"`` the helper substitutes ``""``
            (the String "not set" sentinel).
        alias: Optional UI alias.
        description: Optional UI description.
        is_array: ``True`` for list-typed parameters (used with
            ``IN (SELECT unnest(@arr))`` patterns).

    Example:
        >>> from evergis_tools.layers import declare_eql_parameter, update_layer_eql
        >>> update_layer_eql(client, layer_name,
        ...     eql_query=eql_with_isset_expansions,
        ...     eql_parameters={
        ...         "@category":  declare_eql_parameter("String"),
        ...         "@min_conf":  declare_eql_parameter("Double"),
        ...         "@name_like": declare_eql_parameter("String"),
        ...     })
    """
    attr_type = AttributeType(type_name)
    if default is None and attr_type == AttributeType.STRING:
        default = ""  # String "not set" sentinel; non-String stays None
    return QueryLayerServiceEqlParameterConfigurationDc(
        type=attr_type,
        default=default,
        alias=alias,
        description=description,
        isArray=is_array if is_array else None,
    )


def _convert_eql_parameters(
    eql_parameters: Optional[dict],
) -> Optional[dict]:
    """Convert simple EQL parameter values to QueryLayerServiceEqlParameterConfigurationDc.

    Auto-detects type from Python value:
    - str → String
    - int → Int64
    - float → Double
    - bool → Boolean
    - list → isArray=True + element type

    Args:
        eql_parameters: Simple dict like {"@status": "active", "@count": 10}
                       or dict with QueryLayerServiceEqlParameterConfigurationDc values

    Returns:
        Dict with QueryLayerServiceEqlParameterConfigurationDc values, or None

    Example:
        >>> _convert_eql_parameters({"@status": "active", "@count": 10})
        {
            "@status": QueryLayerServiceEqlParameterConfigurationDc(type=STRING, default="active"),
            "@count": QueryLayerServiceEqlParameterConfigurationDc(type=INT64, default=10)
        }
    """
    if eql_parameters is None:
        return None

    converted = {}
    for key, value in eql_parameters.items():
        # Already a proper config object - pass through
        if isinstance(value, QueryLayerServiceEqlParameterConfigurationDc):
            converted[key] = value
        # Dict that looks like a config - convert to object
        elif isinstance(value, dict) and ("default" in value or "alias" in value or "type" in value):
            converted[key] = QueryLayerServiceEqlParameterConfigurationDc(**value)
        # Simple value - wrap in config with default and auto-detected type
        else:
            is_array = isinstance(value, list)
            # Generate alias from key: "@status" -> "status", "@my_param" -> "my_param"
            alias = key.lstrip("@") if key.startswith("@") else key
            converted[key] = QueryLayerServiceEqlParameterConfigurationDc(
                type=_infer_attribute_type(value),
                isArray=is_array if is_array else None,
                alias=alias,
                default=value,
            )

    return converted


def _normalize_layer_name(client: Client, layer_name: str, log: bool = True) -> str:
    """Normalize and add username prefix to layer name if not present.

    Helper function to ensure layer names have proper format for PostgreSQL table names.
    EverGIS stores layers as PostgreSQL tables in format "usr_<username>.<table_name>".

    Process:
    1. Split username and table name if "." is present
    2. Normalize table name using to_safe_field_name() (transliterate, lowercase, etc.)
    3. Add username prefix if not present
    4. Ensure total length fits PostgreSQL limits (max 63 chars for table name)

    Args:
        client: EverGIS API client (used to get username)
        layer_name: Layer name with or without username prefix
        log: Enable logging output (default True)

    Returns:
        Normalized layer name with username prefix (e.g., "username.my_layer")

    Example:
        >>> _normalize_layer_name(client, "MyLayer")
        'john_doe.my_layer'
        >>> _normalize_layer_name(client, "Мой Слой")
        'john_doe.moi_sloi'
        >>> _normalize_layer_name(client, "john_doe.MyLayer")
        'john_doe.my_layer'
    """
    # Store original name for logging
    original_name = layer_name

    # Get username
    username = client.account.get_user_info().username

    # Check if layer_name already has username prefix
    if "." in layer_name:
        # Split into username and table name
        provided_username, table_name = layer_name.split(".", 1)
        # Use provided username (don't override)
        username = provided_username
    else:
        table_name = layer_name

    # Normalize table name for PostgreSQL
    # PostgreSQL table name limit is 63 characters
    # We need to leave room for potential schema prefix in some cases
    normalized_table_name = to_safe_field_name(
        table_name,
        max_length=63,
        to_snake_case=True,
        allow_numbers_start=False,  # PostgreSQL table names must start with letter
    )

    # Return in format "username.table_name"
    normalized_name = f"{username}.{normalized_table_name}"

    # Log normalization if name changed
    if log and normalized_name != original_name:
        logger.info(f"Layer name normalized: '{original_name}' → '{normalized_name}'")

    return normalized_name


def create_eql_attributes_configuration(
    gdf: "gpd.GeoDataFrame",
    resource_name: str,
    id_attribute: str = "gid",
    geometry_attribute: Optional[str] = None,
    geometry_type: Optional[str] = None,
    order_attribute: Optional[str] = None,
    log: bool = True,
) -> AttributesConfigurationDc:
    """Create AttributesConfigurationDc based on GeoDataFrame schema.

    Args:
        gdf: GeoDataFrame with data
        resource_name: Resource name
        id_attribute: Attribute name for object identification (default "gid")
        geometry_attribute: Geometry attribute name (default "geometry")
        geometry_type: Geometry type (Point, LineString, Polygon, MultiPolygon, etc.)
        log: Enable logging output (default True)

    Returns:
        Attribute configuration for EverGIS API
    """
    if gdf.empty and log:
        logger.warning(f"GeoDataFrame is empty for resource {resource_name}")

    attributes = []
    processed_columns = set()

    # First, add mandatory gid if not present in data
    if id_attribute not in gdf.columns:
        if log:
            logger.info(f"Adding mandatory attribute {id_attribute} for resource {resource_name}")
        attributes.append(
            AttributeConfigurationDc(
                attributeName=id_attribute,
                columnName=id_attribute,
                type=AttributeType.INT64,
                isEditable=False,
            )
        )
        processed_columns.add(id_attribute)

    # Iterate through all DataFrame columns
    for column_name in gdf.columns:
        if column_name in processed_columns:
            continue

        if column_name == geometry_attribute:
            # Process geometry separately
            # If geometry_type is explicitly provided, use it; otherwise auto-detect from data
            geom_type = _convert_geometry_type(
                geometry_type, log=log, fallback=_get_geometry_attribute_type(gdf)
            )

            if geom_type:
                attributes.append(
                    AttributeConfigurationDc(
                        attributeName=geometry_attribute,
                        columnName=geometry_attribute,
                        type=geom_type,
                        isEditable=True,
                    )
                )
        elif column_name == id_attribute:
            # ID attribute supplied in data - keep its values; PK
            # constraints (NOT NULL / UNIQUE / autoincrement) are now
            # derived by the server, the API has no flags for them
            dtype = gdf[column_name].dtype
            attr_type = _pandas_dtype_to_attribute_type(dtype, column_name)
            attributes.append(
                AttributeConfigurationDc(
                    attributeName=column_name,
                    columnName=column_name,
                    type=attr_type,
                    isEditable=False,
                )
            )
        else:
            # Regular attributes
            dtype = gdf[column_name].dtype
            attr_type = _pandas_dtype_to_attribute_type(dtype, column_name)

            attributes.append(
                AttributeConfigurationDc(
                    attributeName=column_name,
                    columnName=column_name,
                    type=attr_type,
                    isEditable=True,
                )
            )

        processed_columns.add(column_name)

    # Determine geometry attribute (only if geometry exists)
    geometry_attr = geometry_attribute if geometry_attribute in gdf.columns else None

    if log:
        logger.info(
            f"Created attribute configuration for {resource_name}: {len(attributes)} attributes"
        )
        logger.info(f"ID attribute: {id_attribute}, Geometry: {geometry_attr}")

    return AttributesConfigurationDc(
        idAttribute=id_attribute,
        geometryAttribute=geometry_attr,
        orderAttribute=order_attribute,
        attributes=attributes,
    )
