from evergis_api import Client
from typing import Any, Dict, Iterable, Optional, Tuple
from evergis_api.schemas import WorkerStartMethodDto

from ...catalog.resources import resolve_resource


def get_csv_data_schema_rest(
    client: Client,
    resource_id: str,
    column_delimiter: str = ";",
    coord_source_fields: Optional[Iterable[str]] = None,
    spatial_reference: int = 4326,
    is_wkt: bool = False,
    attribute_name_row_number: Optional[int] = None,
    alias_row_number: Optional[int] = None,
    first_data_row_number: Optional[int] = None,
) -> Any:
    """
    Get CSV data schema using REST method (importExport/dataSchema).

    This is an alternative to get_import_schema() that uses the worker REST API
    for more control over CSV parsing parameters.

    Args:
        client: EverGIS API client
        resource_id: Catalog path, resource ID, or system name of CSV file
        column_delimiter: Column delimiter character (default ";")
        coord_source_fields: Coordinate field names (optional)
        spatial_reference: Source data SRID (default 4326)
        is_wkt: Flag if CSV contains geometry in WKT format
        attribute_name_row_number: Row number containing attribute names (optional)
        alias_row_number: Row number containing field aliases (optional)
        first_data_row_number: First data row number (optional)

    Returns:
        Schema data returned by the REST method

    Example:
        >>> schema = get_csv_data_schema_rest(
        ...     client,
        ...     "john_doe:Projects/Data/file.csv",
        ...     column_delimiter=";",
        ...     attribute_name_row_number=1,
        ...     first_data_row_number=2
        ... )
    """
    # Resolve resource path to resource_id if needed
    resource = resolve_resource(client, resource_id)
    resolved_resource_id = resource.resourceId

    # Prepare data payload
    data = {
        "source_type": "csv",
        "source_fileName": resolved_resource_id,
        "source_columnDelimiter": column_delimiter,
        "source_spatialReference": spatial_reference,
        "source_isWkt": is_wkt,
    }

    # Add optional fields
    if coord_source_fields:
        data["source_coordSourceFields"] = list(coord_source_fields)
    if attribute_name_row_number is not None:
        data["source_attributeNameRowNumber"] = attribute_name_row_number
    if alias_row_number is not None:
        data["source_aliasRowNumber"] = alias_row_number
    if first_data_row_number is not None:
        data["source_firstDataRowNumber"] = first_data_row_number

    # Create REST method payload
    payload = WorkerStartMethodDto(
        workerType="importExport", methodType="importExport/dataSchema", data=data
    )

    # Call REST method
    return client.remotetaskmanager.post(body=payload)


def get_xlsx_data_schema_rest(
    client: Client,
    resource_id: str,
    coord_source_fields: Optional[Iterable[str]] = None,
    spatial_reference: int = 4326,
    is_wkt: bool = False,
    attribute_name_row_number: Optional[int] = None,
    alias_row_number: Optional[int] = None,
    first_data_row_number: Optional[int] = None,
) -> Any:
    """
    Get XLSX data schema using REST method (importExport/dataSchema).

    This is an alternative to get_import_schema() that uses the worker REST API
    for more control over XLSX parsing parameters.

    Args:
        client: EverGIS API client
        resource_id: Catalog path, resource ID, or system name of XLSX file
        coord_source_fields: Coordinate field names (optional)
        spatial_reference: Source data SRID (default 4326)
        is_wkt: Flag if XLSX contains geometry in WKT format
        attribute_name_row_number: Row number containing attribute names (optional)
        alias_row_number: Row number containing field aliases (optional)
        first_data_row_number: First data row number (optional)

    Returns:
        Schema data returned by the REST method

    Example:
        >>> schema = get_xlsx_data_schema_rest(
        ...     client,
        ...     "john_doe:Projects/Data/file.xlsx",
        ...     attribute_name_row_number=1,
        ...     first_data_row_number=2
        ... )
    """
    # Resolve resource path to resource_id if needed
    resource = resolve_resource(client, resource_id)
    resolved_resource_id = resource.resourceId

    # Prepare data payload
    data = {
        "source_type": "xlsx",
        "source_fileName": resolved_resource_id,
        "source_spatialReference": spatial_reference,
        "source_isWkt": is_wkt,
    }

    # Add optional fields
    if coord_source_fields:
        data["source_coordSourceFields"] = list(coord_source_fields)
    if attribute_name_row_number is not None:
        data["source_attributeNameRowNumber"] = attribute_name_row_number
    if alias_row_number is not None:
        data["source_aliasRowNumber"] = alias_row_number
    if first_data_row_number is not None:
        data["source_firstDataRowNumber"] = first_data_row_number

    # Create REST method payload
    payload = WorkerStartMethodDto(
        workerType="importExport", methodType="importExport/dataSchema", data=data
    )

    # Call REST method
    return client.remotetaskmanager.post(body=payload)


def get_shapefile_data_schema_rest(client: Client, resource_id: str) -> Any:
    """
    Get Shapefile data schema using REST method (importExport/dataSchema).

    This is an alternative to get_import_schema() that uses the worker REST API
    for Shapefile archives.

    Args:
        client: EverGIS API client
        resource_id: Catalog path, resource ID, or system name of Shapefile ZIP archive
        layer_name: Layer name inside the archive (optional, for multi-layer archives)

    Returns:
        Schema data returned by the REST method

    Example:
        >>> schema = get_shapefile_data_schema_rest(
        ...     client,
        ...     "john_doe:Projects/Data/shapefile.zip",
        ...     layer_name="my_layer"
        ... )
    """
    # Resolve resource path to resource_id if needed
    resource = resolve_resource(client, resource_id)
    resolved_resource_id = resource.resourceId

    # Prepare data payload
    data = {
        "source_fileName": resolved_resource_id,
    }

    # Create REST method payload
    payload = WorkerStartMethodDto(
        workerType="importExport", methodType="importExport/dataSchema", data=data
    )

    # print (payload.model_dump_json(indent=2))
    # Call REST method
    return client.remotetaskmanager.post(body=payload)


def get_gpkg_data_schema_rest(
    client: Client,
    resource_id: str,
    layer_name: Optional[str] = None,
) -> Any:
    """
    Get GeoPackage data schema using REST method (importExport/dataSchema).

    A single GPKG is a container with one or more layers. Pass
    ``layer_name`` to get the schema of a specific layer; omit it to
    get the container's table of contents (all layers listed).

    Args:
        client: EverGIS API client.
        resource_id: Catalog path, resource ID, or system name of the
            GPKG file.
        layer_name: Layer name inside the container (optional).

    Returns:
        Schema data returned by the REST method.

    Example:
        >>> # Pick a specific layer
        >>> schema = get_gpkg_data_schema_rest(
        ...     client, "john_doe:.../natural_earth_110m.gpkg", layer_name="countries"
        ... )
        >>> # Or list every layer the container has
        >>> toc = get_gpkg_data_schema_rest(client, "john_doe:.../natural_earth_110m.gpkg")
    """
    resource = resolve_resource(client, resource_id)

    data = {
        "source_type": "gpkg",
        "source_fileName": resource.resourceId,
    }
    if layer_name:
        data["source_layerName"] = layer_name

    payload = WorkerStartMethodDto(
        workerType="importExport", methodType="importExport/dataSchema", data=data
    )
    return client.remotetaskmanager.post(body=payload)


def get_fgdb_data_schema_rest(
    client: Client,
    resource_id: str,
    layer_name: Optional[str] = None,
) -> Any:
    """Get File Geodatabase (FGDB / .gdb) data schema via REST.

    Same shape as :func:`get_gpkg_data_schema_rest` - a FGDB archive
    holds one or more layers. Pass ``layer_name`` to fetch a single
    layer's schema; omit it to get the container's table of contents.

    Args:
        client: EverGIS API client.
        resource_id: Catalog path, resource ID, or system name of the
            FGDB archive (``.gdb.zip``) already uploaded to EverGIS.
        layer_name: Layer name inside the container (optional).

    Returns:
        Schema data returned by the REST method.
    """
    resource = resolve_resource(client, resource_id)

    data = {
        "source_type": "gdb",
        "source_fileName": resource.resourceId,
    }
    if layer_name:
        data["source_layerName"] = layer_name

    payload = WorkerStartMethodDto(
        workerType="importExport", methodType="importExport/dataSchema", data=data
    )
    return client.remotetaskmanager.post(body=payload)


def build_attribute_mappings_from_schema(
    schema: Any,
    layer_name: Optional[str] = None,
    include_geometry: bool = True,
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """Identity attribute mapping + type mapping from a dataSchema response.

    Removes the per-example boilerplate of hand-writing
    ``attribute_mapping`` / ``attribute_type_mapping`` for
    ``import_csv_to_layer`` / ``import_xlsx_to_layer`` /
    ``import_shapefile_to_layer`` / ``import_gpkg_to_layer``.

    Server response shape (uniform across formats - only ``schema['type']``
    differs)::

        schema['layers'][i]['attributesConfiguration']['attributes'] = [
            {'attributeName': '...', 'type': '...',
             'attributeConfigurationType': 'Default' | 'Geometry', ...},
            ...
        ]

    Args:
        schema: Result of ``get_<format>_data_schema_rest``.
        layer_name: Pick a specific layer by name (gpkg/gdb/kml have
            multiple). Defaults to the first layer in the response.
        include_geometry: Keep the geometry attribute in both maps
            (default True).

    Returns:
        ``(attribute_mapping, attribute_type_mapping)`` - both keyed by
        the source field name. ``attribute_mapping`` is identity
        (``{name: name}``); ``attribute_type_mapping`` carries server
        types (``Int32``, ``Double``, ``String``, ``Point``, …).

    Raises:
        ValueError: If the schema has no layers, or ``layer_name`` does
            not match any layer.
    """
    layers = (schema.get("layers") if isinstance(schema, dict) else None) or []
    if not layers:
        raise ValueError("schema has no layers")

    if layer_name:
        layer = next((lyr for lyr in layers if lyr.get("name") == layer_name), None)
        if layer is None:
            available = [lyr.get("name") for lyr in layers]
            raise ValueError(
                f"layer {layer_name!r} not found in schema; "
                f"available: {available}"
            )
    else:
        layer = layers[0]

    attrs = (layer.get("attributesConfiguration") or {}).get("attributes", [])
    attribute_mapping: Dict[str, str] = {}
    attribute_type_mapping: Dict[str, str] = {}
    for a in attrs:
        name = a.get("attributeName")
        if not name:
            continue
        if (
            not include_geometry
            and a.get("attributeConfigurationType") == "Geometry"
        ):
            continue
        attribute_mapping[name] = name
        attribute_type_mapping[name] = a.get("type")
    return attribute_mapping, attribute_type_mapping
