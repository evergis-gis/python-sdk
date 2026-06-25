# -*- coding: utf-8 -*-
"""Layer creation utilities for EverGIS."""

from typing import List, Optional, Any, TYPE_CHECKING
import logging

if TYPE_CHECKING:
    import geopandas as gpd

from evergis_api import Client
from evergis_api.schemas import (
    AttributesConfigurationDc,
    AttributeConfigurationDc,
    QueryLayerServiceConfigurationDc,
    PublishLayerInfoDc,
    LayerServiceType,
    AttributeType,
)

from .._utils import _remove_none_values
from .._errors import raise_conflict_as_exists
from ..attributes import pydantic_to_attribute_type
from ._utils import (
    OverwriteMode,
    _handle_layer_overwrite,
    _convert_geometry_type,
    _convert_eql_parameters,
    _normalize_layer_name,
    create_eql_attributes_configuration,
)

logger = logging.getLogger(__name__)


def gdf_to_layer(
    client: Client,
    gdf: "gpd.GeoDataFrame",
    layer_name: str,
    layer_alias: Optional[str] = None,
    srid: int = 4326,
    id_attribute: str = "gid",
    geometry_attribute: str = "geometry",
    create_table: bool = True,
    overwrite: OverwriteMode = False,
    geometry_type: Optional[str] = None,
    parent_path: Optional[str] = None,
    client_style: Optional[dict] = None,
    order_attribute: Optional[str] = None,
    log: bool = True,
) -> Any:
    """Create layer in EverGIS from GeoDataFrame.

    Args:
        client: EverGIS API client
        gdf: GeoDataFrame with data
        layer_name: Name of the layer to create
        layer_alias: Alias of the layer to create
        srid: Spatial reference system (default 4326)
        id_attribute: Name of attribute for object identification (default "gid")
        geometry_attribute: Name of geometry attribute (default "geometry")
        create_table: Whether to create new table (default True)
        overwrite: Controls overwrite behavior:
            - False: raise error if resources exist
            - True: delete existing resources
            - "cascade": delete existing resources with cascade (removes dependent resources)
        geometry_type: Geometry type (Point, LineString, Polygon, MultiPolygon, etc.)
        parent_path: Catalog path for parent folder (e.g., "owner/Projects/Data").
                    If the path doesn't exist, all missing folders will be created automatically.
        client_style: Mapbox GL style specification (dict, client-side only, not used by server)
        log: Enable logging output (default True)

    Returns:
        Response from server with information about created layer

    Examples:
        >>> from evergis_api import Client
        >>> from evergis_tools.layers import gdf_to_layer
        >>> import geopandas as gpd
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>> gdf = gpd.read_file("data.geojson")
        >>>
        >>> # Example 1: Basic layer creation
        >>> response = gdf_to_layer(
        ...     client=client,
        ...     gdf=gdf,
        ...     layer_name="my_layer",
        ...     parent_path="Projects/Data",
        ...     overwrite=True
        ... )
        >>>
        >>> # Example 2: With Cyrillic name and Mapbox GL style
        >>> style = {
        ...     "items": [{
        ...         "type": "fill",
        ...         "paint": {"fill-color": "#ff0000", "fill-opacity": 0.5}
        ...     }]
        ... }
        >>> response = gdf_to_layer(
        ...     client=client,
        ...     gdf=gdf,
        ...     layer_name="Мои Участки",  # Auto-transliterates to "moi_uchastki"
        ...     layer_alias="Land parcels",
        ...     client_style=style,
        ...     overwrite=True
        ... )
    """
    from ..catalog.folders import get_or_create_folder_by_path

    if log:
        logger.info(f"Creating layer from GeoDataFrame: '{layer_name}'")

    # Normalize layer name (add username prefix, transliterate, lowercase, etc.)
    layer_name = _normalize_layer_name(client, layer_name, log=log)

    # Get or create parent folder if path provided
    parent_id = None
    if parent_path is not None:
        folder = get_or_create_folder_by_path(client=client, path=parent_path)
        parent_id = folder.resourceId
        if log:
            logger.info(f"Using parent folder: {parent_path} (ID: {parent_id})")

    # Create attributes configuration
    attributes_configuration = create_eql_attributes_configuration(
        gdf=gdf,
        resource_name=layer_name,
        id_attribute=id_attribute,
        geometry_attribute=geometry_attribute,
        geometry_type=geometry_type,
        order_attribute=order_attribute,
        log=log,
    )
    # Create layer configuration
    layer_request = QueryLayerServiceConfigurationDc(
        name=layer_name,
        alias=layer_alias or layer_name,  # Layer alias
        eql=f"SELECT * FROM {layer_name}",
        attributesConfiguration=attributes_configuration,
        geometryType=geometry_type,
        createTable=create_table,
        srId=srid,
        parentId=parent_id,
        clientStyle=client_style,
    )

    # Remove None values for cleaner object
    layer_request = _remove_none_values(layer_request)
    if log:
        logger.debug(f"Cleaned request object: {layer_request}")

    response = []

    # Handle overwrite logic using shared helper
    response.extend(
        _handle_layer_overwrite(
            client=client,
            layer_name=layer_name,
            create_table=create_table,
            overwrite=overwrite,
            check_dependencies=False,
            strict_errors=True,  # gdf_to_layer uses strict error handling
            log=log,
        )
    )

    # Create new layer
    try:
        if log:
            logger.info(f"Publishing layer: name={layer_request.name}, create_table={create_table}")
            logger.debug(f"Full request object: {layer_request.model_dump()}")

        layer_request.layerType = LayerServiceType.QUERYLAYERSERVICE
        publish_request = PublishLayerInfoDc(configuration=layer_request)
        response_publish = client.layers.publish_service_async(body=publish_request)
        if log:
            logger.info(f"Layer '{layer_name}' successfully created")
            logger.debug(f"Response: {response_publish}")
        response.append(response_publish)
    except Exception as e:
        if log:
            logger.error(f"Error creating layer '{layer_name}': {e}")
        raise_conflict_as_exists(
            e, resource=f"layer {layer_name!r}",
            alias=layer_alias, parent_path=parent_path,
        )
        raise

    return response


def create_layer_from_schema(
    client: Client,
    schema: type,
    layer_name: str,
    layer_alias: Optional[str] = None,
    srid: int = 4326,
    id_attribute: str = "gid",
    geometry_field: Optional[str] = None,
    geometry_type: Optional[str] = None,
    overwrite: OverwriteMode = False,
    parent_path: Optional[str] = None,
    client_style: Optional[dict] = None,
    card_configuration: Optional[dict] = None,
    edit_configuration: Optional[dict] = None,
    create_table: bool = True,
    query: Optional[str] = None,
    ds: Optional[str] = None,
    order_attribute: Optional[str] = None,
    extra_attributes: Optional[List[AttributeConfigurationDc]] = None,
    log: bool = True,
) -> Any:
    """Create EverGIS layer directly from Pydantic schema.

    Args:
        client: EverGIS API client
        schema: Pydantic model class (BaseModel subclass)
        layer_name: Name of the layer to create
        layer_alias: Alias of the layer to create (defaults to layer_name)
        srid: Spatial reference system (default 4326)
        id_attribute: Name of attribute for object identification (default "gid")
        geometry_field: Name of geometry field in schema (optional)
        geometry_type: Geometry type: Point, LineString, Polygon, MultiPolygon, etc. (optional)
        overwrite: Controls overwrite behavior:
            - False: raise error if resources exist
            - True: delete existing resources
            - "cascade": delete existing resources with cascade (removes dependent resources)
        parent_path: Catalog path for parent folder (e.g., "owner/Projects/Data")
        client_style: Mapbox GL style specification (dict, client-side only, not used by server)
        card_configuration: Card configuration for feature display (dict, client-side only, not used by server)
        edit_configuration: Edit form configuration (dict, client-side only, not used by server)
        create_table: Whether to create physical table (default True). If False, creates virtual layer
        query: Custom EQL query (required when create_table=False). If provided, used instead of default SELECT
        ds: External DataSource name to bind the layer to (e.g. a Postgres
            connection created via ``create_postgres_data_source``). When
            omitted the layer uses the instance's default data source.
        log: Enable logging output (default True)

    Returns:
        Response from server with information about created layer

    Notes:
        - Geometry support:
          1. Explicit: geometry_field="geometry", geometry_type="Point"
          2. Field metadata: Field(json_schema_extra={"geometry_type": "Point"})
          3. Auto-detect: if field name is "geometry", defaults to Point
        - For Optional fields, the non-None inner type is used
        - list and dict types are converted to JSON attribute type

    Examples:
        >>> from evergis_api import Client
        >>> from evergis_tools.layers import create_layer_from_schema
        >>> from pydantic import BaseModel, Field
        >>> from typing import Optional
        >>>
        >>> # Example 1: Simple table without geometry
        >>> class BuildingSchema(BaseModel):
        ...     name: str = Field(description="Building name")
        ...     floors: int = Field(description="Number of floors")
        ...     year_built: Optional[int] = None
        ...
        >>> client = Client(base_url="...", sb_token="...")
        >>> response = create_layer_from_schema(
        ...     client=client,
        ...     schema=BuildingSchema,
        ...     layer_name="buildings_table",
        ...     parent_path="Projects/Data"
        ... )
        >>>
        >>> # Example 2: Layer with geometry and Cyrillic name
        >>> class ParcelSchema(BaseModel):
        ...     cad_num: str = Field(description="Cadastral number")
        ...     area: float = Field(description="Area (sq. m)")
        ...     geometry: str = Field(description="Parcel geometry")
        ...
        >>> response = create_layer_from_schema(
        ...     client=client,
        ...     schema=ParcelSchema,
        ...     layer_name="Земельные Участки",  # Auto-transliterates to "zemelnye_uchastki"
        ...     layer_alias="Cadastral parcels",
        ...     geometry_field="geometry",
        ...     geometry_type="Polygon",
        ...     srid=4326,
        ...     overwrite=True
        ... )
        >>>
        >>> # Example 3: Virtual layer with custom EQL query (no physical table)
        >>> class FilteredParcelSchema(BaseModel):
        ...     cad_num: str = Field(description="Cadastral number")
        ...     area: float = Field(description="Area (sq. m)")
        ...     geometry: str = Field(description="Parcel geometry")
        ...
        >>> response = create_layer_from_schema(
        ...     client=client,
        ...     schema=FilteredParcelSchema,
        ...     layer_name="expensive_parcels",
        ...     layer_alias="Expensive parcels",
        ...     geometry_field="geometry",
        ...     geometry_type="Polygon",
        ...     create_table=False,
        ...     query="SELECT * FROM username.parcels WHERE price > 10000000",
        ...     overwrite=True
        ... )
    """
    from ..catalog.folders import get_or_create_folder_by_path

    if log:
        logger.info(f"Creating layer from schema {schema.__name__}: '{layer_name}'")

    # Validate query parameter
    if not create_table and query is None:
        raise ValueError("The query parameter is required when create_table=False")

    # Normalize layer name (add username prefix, transliterate, lowercase, etc.)
    layer_name = _normalize_layer_name(client, layer_name, log=log)

    # Get or create parent folder if path provided
    parent_id = None
    if parent_path is not None:
        folder = get_or_create_folder_by_path(client=client, path=parent_path)
        parent_id = folder.resourceId
        if log:
            logger.info(f"Using parent folder: {parent_path} (ID: {parent_id})")

    # Extract fields from Pydantic schema
    schema_fields = schema.model_fields
    attributes = []
    processed_fields = set()

    # Add mandatory gid if not present in schema
    if id_attribute not in schema_fields:
        if log:
            logger.info(f"Adding mandatory attribute {id_attribute}")
        attributes.append(
            AttributeConfigurationDc(
                attributeName=id_attribute,
                columnName=id_attribute,
                type=AttributeType.INT64,
                isEditable=False,
            )
        )
        processed_fields.add(id_attribute)

    # Process schema fields
    geometry_attribute_name = None
    geometry_type_attr = None

    for field_name, field_info in schema_fields.items():
        if field_name in processed_fields:
            continue

        # Check if this is geometry field
        is_geometry = False
        field_geometry_type = None

        if geometry_field and field_name == geometry_field:
            # Explicitly specified geometry field
            is_geometry = True
            field_geometry_type = geometry_type

        # Check Field metadata for geometry / sub_type / attribute_type info
        field_sub_type = None
        field_attr_type = None
        if field_info.json_schema_extra:
            extra = field_info.json_schema_extra
            if isinstance(extra, dict):
                if "geometry_type" in extra:
                    is_geometry = True
                    field_geometry_type = extra["geometry_type"]
                if "sub_type" in extra:
                    field_sub_type = extra["sub_type"]
                if "attribute_type" in extra:
                    field_attr_type = extra["attribute_type"]

        # Auto-detect geometry by field name
        if field_name == "geometry" and not is_geometry:
            is_geometry = True
            field_geometry_type = field_geometry_type or "Point"

        # Typed sub_type fields (Attachments today; Image / PkkCode etc.
        # later) are produced by builders registered in attribute_types.
        # ``create.py`` itself stays agnostic - adding a new sub_type means
        # a new file under attribute_types/ and a @register_sub_type
        # decorator there. Publishing such a layer requires
        # ``serialize_as_any=True`` so the subclass-specific fields survive
        # serialization through the un-discriminated Union (handled below).
        if field_sub_type:
            from ..attribute_types import SUB_TYPE_BUILDERS

            builder = SUB_TYPE_BUILDERS.get(field_sub_type)
            if builder is None:
                raise ValueError(
                    f"Unknown sub_type {field_sub_type!r} on field "
                    f"{field_name!r}. Known: {sorted(SUB_TYPE_BUILDERS)}"
                )
            attributes.append(builder(field_name, field_info))
            processed_fields.add(field_name)
            continue

        if is_geometry:
            # Process geometry field
            geom_type = _convert_geometry_type(
                field_geometry_type, log=log, fallback=AttributeType.POINT
            )

            # Get description from field for alias
            field_alias = field_info.description if field_info.description else None

            attributes.append(
                AttributeConfigurationDc(
                    attributeName=field_name,
                    columnName=field_name,
                    type=geom_type,
                    alias=field_alias,
                    isEditable=True,
                )
            )
            geometry_attribute_name = field_name
            geometry_type_attr = geom_type
        elif field_name == id_attribute:
            # Identifier supplied in schema (any name, not just "gid").
            # The PK is Int64: plain ``int`` now defaults to Int32, so bump
            # it back to Int64 here. PK constraints (NOT NULL / UNIQUE /
            # autoincrement) are derived by the server - the API has no
            # flags for them. A non-integer id (e.g. String) is left as-is.
            field_type = field_info.annotation
            attr_type = pydantic_to_attribute_type(field_type, field_name)
            if attr_type == AttributeType.INT32:
                attr_type = AttributeType.INT64
            field_alias = field_info.description if field_info.description else None

            attributes.append(
                AttributeConfigurationDc(
                    attributeName=field_name,
                    columnName=field_name,
                    type=attr_type,
                    alias=field_alias,
                    isEditable=False,
                )
            )
        else:
            # Regular attribute. An explicit ``attribute_type`` in
            # ``Field(json_schema_extra=...)`` overrides the Python-type
            # mapping - e.g. force ``Int32``, since the default for ``int``
            # is ``Int64`` which the server now treats as an autoincrement
            # PK (so a user Int64 column rejects NULLs).
            field_type = field_info.annotation
            attr_type = (
                AttributeType(field_attr_type)
                if field_attr_type
                else pydantic_to_attribute_type(field_type, field_name)
            )

            # Get description from field for alias
            field_alias = field_info.description if field_info.description else None

            attributes.append(
                AttributeConfigurationDc(
                    attributeName=field_name,
                    columnName=field_name,
                    type=attr_type,
                    alias=field_alias,
                    isEditable=True,
                )
            )

        processed_fields.add(field_name)

    # If geometry_field is specified but not found in schema, create it
    if geometry_field and geometry_field not in processed_fields:
        if log:
            logger.info(f"Adding geometry field '{geometry_field}' (not in schema)")

        # Determine geometry type
        geom_type = _convert_geometry_type(geometry_type, log=log, fallback=AttributeType.POINT)

        attributes.append(
            AttributeConfigurationDc(
                attributeName=geometry_field,
                columnName=geometry_field,
                type=geom_type,
                isEditable=True,
            )
        )
        geometry_attribute_name = geometry_field
        geometry_type_attr = geom_type

    # Append explicit subtype-aware attributes (e.g. AttachmentsAttribute).
    # They are not derived from the Pydantic schema, so the caller passes
    # ready-made AttributeConfigurationDc subclasses.
    if extra_attributes:
        existing_names = {a.attributeName for a in attributes}
        for attr in extra_attributes:
            if attr.attributeName in existing_names:
                if log:
                    logger.warning(
                        f"extra_attributes: skipping {attr.attributeName!r} - "
                        "schema already defines a column with this name"
                    )
                continue
            attributes.append(attr)
            existing_names.add(attr.attributeName)

    # Create attributes configuration
    attributes_configuration = AttributesConfigurationDc(
        idAttribute=id_attribute,
        geometryAttribute=geometry_attribute_name,
        orderAttribute=order_attribute,
        tableName=layer_name,
        attributes=attributes,
    )

    # Table-only schema (no geometry field). The server still wants
    # ``geometryType="Unknown"`` for this case - leaving it as ``null``
    # makes POST /layers return a 500-flavoured 400. The same call from
    # the EverGIS UI also drops srId for table-only layers; mirror that
    # so we don't ship a meaningless SRID alongside ``geometryType=Unknown``.
    if geometry_type_attr is None:
        geometry_type_attr = "Unknown"
        srid = None

    # Create layer configuration
    layer_request = QueryLayerServiceConfigurationDc(
        name=layer_name,
        alias=layer_alias if layer_alias else layer_name,
        eql=query if query else f"SELECT * FROM {layer_name}",
        attributesConfiguration=attributes_configuration,
        geometryType=geometry_type_attr,
        createTable=create_table,
        srId=srid,
        parentId=parent_id,
        clientStyle=client_style,
        cardConfiguration=card_configuration,
        editConfiguration=edit_configuration,
        ds=ds,
    )

    # Note: previously this stage ran ``_remove_none_values(layer_request)``
    # which dumped the root and re-validated it. That re-validation collapsed
    # any AttributeConfigurationDc subclass back to the base type via the
    # un-discriminated ``attributes`` Union, dropping subType / etc. We rely
    # on ``model_dump(exclude_unset=True)`` at publish time instead - it
    # already strips fields the caller did not explicitly set.

    response = []

    # Handle overwrite logic using shared helper
    response.extend(
        _handle_layer_overwrite(
            client=client,
            layer_name=layer_name,
            create_table=create_table,
            overwrite=overwrite,
            check_dependencies=False,
            strict_errors=False,  # create_layer_from_schema propagates exceptions
            log=log,
        )
    )

    # Publish via raw HTTP because the generated ``publish_service_async``
    # serializes the body with ``model_dump(exclude_unset=True)`` only -
    # without ``serialize_as_any=True`` the un-discriminated
    # ``AttributesConfigurationDc.attributes`` Union strips fields of any
    # subclass (e.g. AttachmentsAttribute.subType). ``by_alias=True`` keeps
    # the snake_case fields we declared with ``alias=`` in
    # camelCase that the server expects.
    try:
        if log:
            logger.info(f"Publishing layer: name={layer_request.name}, create_table={create_table}")
            logger.debug(f"Full request object: {layer_request.model_dump()}")

        layer_request.layerType = LayerServiceType.QUERYLAYERSERVICE
        publish_request = PublishLayerInfoDc(configuration=layer_request)
        publish_payload = publish_request.model_dump(
            exclude_unset=True,
            serialize_as_any=True,
            by_alias=True,
            mode="json",
        )
        response_publish = client._request("post", "/layers", json=publish_payload)
        if log:
            logger.info(f"Layer '{layer_name}' successfully created")
            logger.debug(f"Response: {response_publish}")
        response.append(response_publish)
    except Exception as e:
        if log:
            logger.error(f"Error creating layer '{layer_name}': {e}")
        raise_conflict_as_exists(
            e, resource=f"layer {layer_name!r}",
            alias=layer_alias, parent_path=parent_path,
        )
        raise

    return response


def create_query_layer(
    client: Client,
    layer_name: str,
    eql_query: str,
    *,
    layer_alias: Optional[str] = None,
    parent_path: Optional[str] = None,
    geometry_type: Optional[Any] = None,
    srid: int = 4326,
    id_attribute: str = "gid",
    geometry_attribute: str = "geometry",
    create_table: bool = False,
    overwrite: OverwriteMode = False,
    description: Optional[str] = None,
    condition: Optional[str] = None,
    eql_parameters: Optional[dict] = None,
    client_style: Optional[dict] = None,
    card_configuration: Optional[dict] = None,
    edit_configuration: Optional[dict] = None,
    ds: Optional[str] = None,
    order_attribute: Optional[str] = None,
    log: bool = True,
) -> Any:
    """Create a query layer (virtual layer) from EQL query.

    Creates a layer defined by an EQL query without requiring physical table storage
    (unless create_table=True). This is useful for:
    - Virtual views of existing data
    - Filtered layers with permanent WHERE conditions
    - Joined data from multiple tables
    - Computed columns via EQL expressions

    Args:
        client: EverGIS API client
        layer_name: Layer name (username prefix will be added automatically if not present)
        eql_query: EQL query defining the layer data (e.g., "SELECT * FROM table WHERE condition")
        layer_alias: Human-readable layer name (optional)
        parent_path: Parent folder path (e.g., "username:Projects/Layers")
        geometry_type: Geometry type (Point, Polygon, MultiPolygon, etc.) as string or AttributeType
        srid: Spatial reference ID (default 4326 = WGS84)
        id_attribute: ID attribute name (default "gid")
        geometry_attribute: Geometry attribute name (default "geometry")
        create_table: If True, creates physical table; if False, creates virtual layer only
        overwrite: Controls overwrite behavior:
            - False: raise error if layer exists
            - True: delete existing layer (and dependent tables if create_table=True)
            - "cascade": delete existing layer with cascade (removes all dependent resources)
        description: Layer description
        condition: Additional filter condition (WHERE clause)
        eql_parameters: EQL parameters for parameterized queries (e.g., {"@status": "active"})
        client_style: Mapbox GL style specification (dict, client-side only, not used by server)
        card_configuration: Card configuration for feature display (dict, client-side only, not used by server)
        edit_configuration: Edit form configuration (dict, client-side only, not used by server)
        ds: External DataSource name to bind the layer to (e.g. a Postgres
            connection from ``create_postgres_data_source``). Omit to use
            the instance's default data source.
        log: Enable logging (default True)

    Returns:
        QueryLayerServiceInfoDc with created layer information

    Examples:
        >>> # Example 1: Simple virtual layer with filter
        >>> result = create_query_layer(
        ...     client=client,
        ...     layer_name="expensive_parcels",
        ...     eql_query="SELECT * FROM username.parcels WHERE cost_value > 10000000",
        ...     geometry_type="Polygon",
        ...     layer_alias="Expensive parcels",
        ...     overwrite=True
        ... )
        >>>
        >>> # Example 2: With EQL parameters and Mapbox style
        >>> style = {
        ...     "items": [{
        ...         "type": "fill",
        ...         "paint": {"fill-color": "#0000ff", "fill-opacity": 0.3}
        ...     }]
        ... }
        >>> result = create_query_layer(
        ...     client=client,
        ...     layer_name="Здания Города",  # Auto-transliterates to "zdaniya_goroda"
        ...     eql_query="SELECT * FROM username.buildings WHERE city = @city",
        ...     eql_parameters={"@city": "Moscow"},
        ...     geometry_type="Polygon",
        ...     layer_alias="Buildings in Moscow",
        ...     client_style=style,
        ...     parent_path="Projects/Layers",
        ...     overwrite=True
        ... )
    """
    # Import here to avoid circular dependencies
    from ..catalog.folders import get_or_create_folder_by_path

    if log:
        logger.info(f"Creating query layer: '{layer_name}'")

    # Normalize layer name (add username prefix, transliterate, lowercase, etc.)
    full_layer_name = _normalize_layer_name(client, layer_name, log=log)

    # Handle overwrite logic using shared helper
    _handle_layer_overwrite(
        client=client,
        layer_name=full_layer_name,
        create_table=create_table,
        overwrite=overwrite,
        check_dependencies=create_table,  # Only check dependencies if creating table
        strict_errors=False,  # create_query_layer uses lenient error handling
        log=log,
    )

    # Convert geometry_type to AttributeType if it's a string
    geometry_type_attr = _convert_geometry_type(geometry_type, log=log, fallback=None)

    # Get or create parent folder if path provided
    parent_id = None
    if parent_path is not None:
        folder = get_or_create_folder_by_path(client=client, path=parent_path)
        parent_id = folder.resourceId
        if log:
            logger.info(f"Using parent folder: {parent_path} (ID: {parent_id})")

    # Build attributes configuration automatically
    # For query layers, we typically let the API infer the schema from the EQL query
    # However, we need to provide at least the basic structure
    attributes_config = AttributesConfigurationDc(
        idAttribute=id_attribute,
        geometryAttribute=geometry_attribute if geometry_type else None,
        orderAttribute=order_attribute,
        tableName=full_layer_name,  # Table name for the query layer
    )

    # Convert EQL parameters to proper format
    converted_eql_parameters = _convert_eql_parameters(eql_parameters)

    # Create layer configuration
    layer_config = QueryLayerServiceConfigurationDc(
        name=full_layer_name,
        eql=eql_query,
        attributesConfiguration=attributes_config,
        geometryType=geometry_type_attr,
        srId=srid,
        createTable=create_table,
        alias=layer_alias,
        description=description,
        parentId=parent_id,
        condition=condition,
        eqlParameters=converted_eql_parameters,
        clientStyle=client_style,
        cardConfiguration=card_configuration,
        editConfiguration=edit_configuration,
        ds=ds,
    )

    # Remove None values to avoid API issues
    layer_config_dict = _remove_none_values(layer_config.model_dump())
    layer_config = QueryLayerServiceConfigurationDc(**layer_config_dict)
    try:
        if log:
            logger.info(
                f"Publishing query layer: name={full_layer_name}, create_table={create_table}"
            )
            logger.debug(f"EQL query: {eql_query}")
            logger.debug(f"Full configuration: {layer_config.model_dump()}")

        layer_config.layerType = LayerServiceType.QUERYLAYERSERVICE
        publish_request = PublishLayerInfoDc(configuration=layer_config)
        response = client.layers.publish_service_async(body=publish_request)

        if log:
            logger.info(f"Query layer '{full_layer_name}' created successfully")
            logger.debug(f"Response: {response}")

        return response
    except Exception as e:
        if log:
            logger.error(f"Error creating query layer '{full_layer_name}': {e}")
        raise_conflict_as_exists(
            e, resource=f"query layer {full_layer_name!r}",
            alias=layer_alias, parent_path=parent_path,
        )
        raise
