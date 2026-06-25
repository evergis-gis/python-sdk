# -*- coding: utf-8 -*-
"""Layer reading utilities for EverGIS."""

from typing import Optional, Dict
import json
import logging

from pydantic import ValidationError

from evergis_api import Client
from evergis_api.schemas import (
    AttributesConfigurationDc,
    QueryLayerServiceConfigurationDc,
)
from evergis_api._generated.exceptions import ApiClientError

from ._utils import _normalize_layer_name, _convert_geometry_type

logger = logging.getLogger(__name__)


def get_layer_schema(
    client: Client, layer_name: str, log: bool = True
) -> Optional[AttributesConfigurationDc]:
    """Get layer schema definition including attributes and geometry information.

    Args:
        client: EverGIS API client
        layer_name: Layer name (with or without username prefix)
        log: Enable logging

    Returns:
        AttributesConfigurationDc with attributes dict, geometry type, etc., or None if not available

    Raises:
        ApiClientError: If layer doesn't exist or API request fails

    Example:
        >>> from evergis_api import Client
        >>> client = Client(host="https://api.example.com", token="...")
        >>> schema = get_layer_schema(client, "username.my_layer")
        >>> if schema and schema.attributes:
        ...     for attr in schema.attributes:
        ...         print(f"{attr.attributeName}: {attr.type}")
    """
    # Normalize layer name to full format
    layer_name = _normalize_layer_name(client, layer_name, log=log)

    if log:
        logger.info(f"Fetching schema for layer '{layer_name}'")

    try:
        # Try to get layer info using the generated client method
        layer_info = client.layers.get_layer_info_async(name=layer_name)

        # Extract layerDefinition from response
        # Different service types have different structures
        layer_definition = None

        if hasattr(layer_info, "layerDefinition"):
            layer_definition = layer_info.layerDefinition
        elif hasattr(layer_info, "configuration"):
            # Some layer types have configuration.layerDefinition
            config = layer_info.configuration
            if hasattr(config, "layerDefinition"):
                layer_definition = config.layerDefinition

        if not layer_definition:
            if log:
                logger.warning(f"Layer '{layer_name}' info does not contain layerDefinition")
            return None

        if log:
            attr_count = len(layer_definition.attributes) if layer_definition.attributes else 0
            logger.info(
                f"Retrieved schema for '{layer_name}': {attr_count} attributes, geometry: {layer_definition.geometryType}"
            )

        return layer_definition

    except ValidationError as e:
        # Validation failed because the actual response type (e.g., QueryLayerServiceInfoDc)
        # is not in the Union[ServiceInfoDc, ResourceInfoDc] that the generated client expects.
        # Fall back to parsing raw JSON directly.
        if log:
            logger.debug(
                f"Pydantic validation failed for layer '{layer_name}' info, "
                "falling back to raw JSON parsing"
            )

        try:
            # Make a direct HTTP request to get raw JSON
            path = f"/layers/{layer_name}"
            response = client._request("get", path)
            layer_info_dict = json.loads(response.content)

            # Extract layerDefinition from raw dict
            layer_definition_dict = None
            if "layerDefinition" in layer_info_dict:
                layer_definition_dict = layer_info_dict["layerDefinition"]
            elif "configuration" in layer_info_dict:
                config = layer_info_dict["configuration"]
                if isinstance(config, dict) and "layerDefinition" in config:
                    layer_definition_dict = config["layerDefinition"]

            if not layer_definition_dict:
                if log:
                    logger.warning(
                        f"Layer '{layer_name}' info does not contain layerDefinition in raw JSON"
                    )
                return None

            # Parse layerDefinition using Pydantic
            layer_definition = AttributesConfigurationDc.model_validate(layer_definition_dict)

            if log:
                attr_count = len(layer_definition.attributes) if layer_definition.attributes else 0
                logger.info(
                    f"Retrieved schema for '{layer_name}': {attr_count} attributes, "
                    f"geometry: {layer_definition.geometryType}"
                )

            return layer_definition

        except Exception as fallback_error:
            if log:
                logger.error(
                    f"Failed to parse layer '{layer_name}' schema from raw JSON: {fallback_error}"
                )
            # Re-raise the original ValidationError since fallback also failed
            raise e from fallback_error

    except ApiClientError as e:
        if log:
            logger.error(f"Failed to get schema for layer '{layer_name}': {e}")
        raise


def get_layer_configuration(
    client: Client,
    layer_name: str,
    log: bool = True,
) -> QueryLayerServiceConfigurationDc:
    """Get full layer configuration for QueryLayerService.

    Retrieves the complete configuration of a query layer including EQL query,
    parameters, style, card configuration, edit configuration, and attributes.

    Args:
        client: EverGIS API client
        layer_name: Layer name (with or without username prefix)
        log: Enable logging

    Returns:
        QueryLayerServiceConfigurationDc with current layer configuration

    Raises:
        ApiClientError: If layer doesn't exist or API request fails
        ValueError: If layer is not a QueryLayerService

    Example:
        >>> from evergis_api import Client
        >>> from evergis_tools.layers import get_layer_configuration
        >>>
        >>> client = Client(base_url="...", sb_token="...")
        >>> config = get_layer_configuration(client, "my_layer")
        >>> print(config.eql)
        >>> print(config.clientStyle)
    """
    # Normalize layer name to full format
    layer_name = _normalize_layer_name(client, layer_name, log=log)

    if log:
        logger.info(f"Fetching configuration for layer '{layer_name}'")

    try:
        # Make a direct HTTP request to get raw JSON
        # This avoids validation issues with the generated client
        path = f"/layers/{layer_name}"
        response = client._request("get", path)
        layer_info_dict = json.loads(response.content)

        # Extract configuration from nested field
        config_dict = layer_info_dict.get("configuration", {})

        # Check if this is a QueryLayerService
        # New API: configuration.layerType, old API: top-level "type"
        layer_type = (
            config_dict.get("layerType")
            or layer_info_dict.get("type")
        )
        if layer_type != "QueryLayerService":
            raise ValueError(
                f"Layer '{layer_name}' is not a QueryLayerService (type: {layer_type}). "
                "Only QueryLayerService layers can be configured with these functions."
            )

        # Normalize geometryType (API returns lowercase "multipolygon", enum expects "MultiPolygon")
        if "geometryType" in config_dict and config_dict["geometryType"]:
            geom_type = config_dict["geometryType"]
            geom_type_enum = _convert_geometry_type(geom_type, log=False)
            config_dict["geometryType"] = geom_type_enum.value if geom_type_enum else None

        # Parse as QueryLayerServiceConfigurationDc
        config = QueryLayerServiceConfigurationDc.model_validate(config_dict)

        if log:
            logger.info(f"Retrieved configuration for layer '{layer_name}'")
            logger.debug(f"EQL: {config.eql[:100]}..." if config.eql and len(config.eql) > 100 else f"EQL: {config.eql}")

        return config

    except ApiClientError as e:
        if log:
            logger.error(f"Failed to get configuration for layer '{layer_name}': {e}")
        raise


def create_identity_mapping_from_layer(
    client: Client,
    layer_name: str,
    exclude_geometry: bool = False,
    log: bool = True
) -> Dict[str, str]:
    """Create identity attribute mapping for export (field_name -> field_name).

    This function creates a simple mapping where each field maps to itself,
    useful for exporting all layer attributes without renaming.

    Args:
        client: EverGIS API client
        layer_name: Layer name (with or without username prefix)
        exclude_geometry: Exclude geometry field from mapping (default: False)
        log: Enable logging (default: True)

    Returns:
        Dictionary mapping {field_name: field_name} for all layer attributes

    Raises:
        ValueError: If layer has no attributes
        ApiClientError: If layer doesn't exist or API request fails

    Example:
        >>> from evergis_api import Client
        >>> from evergis_tools import create_identity_mapping_from_layer
        >>> client = Client(host="https://api.example.com", token="...")
        >>>
        >>> # Get identity mapping for export
        >>> mapping = create_identity_mapping_from_layer(client, "username.cities")
        >>> mapping
        {'gid': 'gid', 'name': 'name', 'population': 'population', 'geometry': 'geometry'}
        >>>
        >>> # Use in export
        >>> from evergis_tools.tasks.export_tools import export_layer_to_xlsx
        >>> result = export_layer_to_xlsx(
        ...     client=client,
        ...     source_layer="username.cities",
        ...     target_file_name="cities_export.xlsx",
        ...     target_parent_path="username:Exports",
        ...     attribute_mapping=mapping
        ... )
    """
    # Get layer schema
    schema = get_layer_schema(client, layer_name, log=log)

    if not schema or not schema.attributes:
        raise ValueError(f"Layer '{layer_name}' has no attributes")

    # Create identity mapping
    mapping = {}
    geometry_attr = schema.geometryAttribute or "geometry"

    for attr in schema.attributes:
        field_name = attr.attributeName
        # Skip geometry if excluded
        if exclude_geometry and field_name == geometry_attr:
            continue

        # Identity mapping: field -> field
        mapping[field_name] = field_name

    if log:
        field_count = len(mapping)
        logger.info(f"Created identity mapping for '{layer_name}': {field_count} fields")

    return mapping


def create_export_mappings_from_layer(
    client: Client,
    layer_name: str,
    exclude_geometry: bool = False,
    log: bool = True,
) -> tuple[Dict[str, str], Dict[str, str]]:
    """Build ``(attribute_mapping, attribute_type_mapping)`` from a layer.

    Some server-side export handlers (``LayerToGeojson``,
    ``LayerToGpkg``) crash with a null-reference exception when these
    two maps are missing. Building them by hand is repetitive - this
    helper reads the layer schema and returns ready-to-pass identity
    mapping plus the matching ``{field: EverGISType}`` dict.

    Args:
        client: EverGIS API client.
        layer_name: Layer name (with or without username prefix).
        exclude_geometry: Drop the geometry field from both maps.
        log: Enable info logging.

    Returns:
        Tuple ``(attribute_mapping, attribute_type_mapping)``.

    Example:
        >>> attr_map, type_map = create_export_mappings_from_layer(
        ...     client, "john_doe.evg_overture_metro_stations"
        ... )
        >>> result = export_layer_to_geojson(
        ...     client=client,
        ...     source_layer="john_doe.evg_overture_metro_stations",
        ...     target_file_name="metro.geojson",
        ...     target_parent_path="john_doe:Projects/Exports",
        ...     attribute_mapping=attr_map,
        ...     attribute_type_mapping=type_map,
        ... )
    """
    # ``get_layer_schema`` reads through ``layerDefinition``, which is
    # absent on ``QueryLayerService`` layers - fall through to the
    # ``configuration.attributesConfiguration`` block instead, which is
    # populated for every layer type.
    layer_name = _normalize_layer_name(client, layer_name, log=log)
    info = client.layers.get_layer_info_async(name=layer_name)
    ac = getattr(getattr(info, "configuration", None), "attributesConfiguration", None)
    attributes = getattr(ac, "attributes", None) if ac else None
    if not attributes:
        raise ValueError(f"Layer '{layer_name}' has no attributes")

    geometry_attr = getattr(ac, "geometryAttribute", None) or "geometry"
    mapping: Dict[str, str] = {}
    type_mapping: Dict[str, str] = {}
    for attr in attributes:
        name = attr.attributeName
        if exclude_geometry and name == geometry_attr:
            continue
        mapping[name] = name
        type_mapping[name] = str(attr.type) if attr.type is not None else "String"

    if log:
        logger.info(
            f"Created export mappings for '{layer_name}': {len(mapping)} fields"
        )
    return mapping, type_mapping
