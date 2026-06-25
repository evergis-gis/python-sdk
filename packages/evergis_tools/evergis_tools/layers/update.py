# -*- coding: utf-8 -*-
"""Layer update utilities for EverGIS."""

from typing import Optional, Any, Dict
import logging

from evergis_api import Client
from evergis_api.schemas import (
    AttributeConfigurationDc,
    AttributesConfigurationDc,
    QueryLayerServiceConfigurationDc,
)

from .._utils import _remove_none_values
from ._utils import _normalize_layer_name, _convert_eql_parameters
from .read import get_layer_configuration

logger = logging.getLogger(__name__)


def update_layer_configuration(
    client: Client,
    layer_name: str,
    configuration: QueryLayerServiceConfigurationDc,
    log: bool = True,
) -> Any:
    """Update full layer configuration.

    Replaces the entire layer configuration with the provided one.
    Use get_layer_configuration() to get current config, modify it,
    then pass to this function.

    Args:
        client: EverGIS API client
        layer_name: Layer name (with or without username prefix)
        configuration: New configuration (QueryLayerServiceConfigurationDc)
        log: Enable logging

    Returns:
        API response with updated layer info

    Raises:
        ApiClientError: If layer doesn't exist or update fails

    Example:
        >>> config = get_layer_configuration(client, "my_layer")
        >>> config.alias = "New Layer Name"
        >>> config.description = "Updated description"
        >>> update_layer_configuration(client, "my_layer", config)
    """
    if log:
        logger.info(f"Updating full configuration for layer '{layer_name}'")

    # Normalize layer name
    layer_name = _normalize_layer_name(client, layer_name, log=log)

    # Ensure name matches
    configuration.name = layer_name

    # Remove None values
    config_dict = _remove_none_values(configuration.model_dump())
    updated_config = QueryLayerServiceConfigurationDc(**config_dict)

    try:
        response = client.layers.patch_query_layer_service(
            name=layer_name,
            body=updated_config
        )
        if log:
            logger.info(f"Layer '{layer_name}' configuration updated successfully")
        return response
    except Exception as e:
        if log:
            logger.error(f"Error updating configuration for layer '{layer_name}': {e}")
        raise


def update_layer_eql(
    client: Client,
    layer_name: str,
    eql_query: Optional[str] = None,
    eql_parameters: Optional[Dict[str, Any]] = None,
    condition: Optional[str] = None,
    log: bool = True,
) -> Any:
    """Update EQL query and/or parameters for a layer.

    Updates only the EQL-related fields without affecting other configuration.
    At least one of eql_query, eql_parameters, or condition must be provided.

    Args:
        client: EverGIS API client
        layer_name: Layer name (with or without username prefix)
        eql_query: New EQL query (optional)
        eql_parameters: New EQL parameters dict (optional)
        condition: Additional filter condition (optional)
        log: Enable logging

    Returns:
        API response with updated layer info

    Raises:
        ValueError: If no parameters are provided
        ApiClientError: If layer doesn't exist or update fails

    Example:
        >>> # Update only parameters
        >>> update_layer_eql(
        ...     client, "my_layer",
        ...     eql_parameters={"@status": "active", "@region": "Moscow"}
        ... )
        >>>
        >>> # Update query and parameters
        >>> update_layer_eql(
        ...     client, "my_layer",
        ...     eql_query="SELECT * FROM table WHERE status = @status",
        ...     eql_parameters={"@status": "active"}
        ... )
        >>>
        >>> # Clear parameters (set empty dict)
        >>> update_layer_eql(client, "my_layer", eql_parameters={})
    """
    if eql_query is None and eql_parameters is None and condition is None:
        raise ValueError("At least one of eql_query, eql_parameters, or condition must be provided")

    if log:
        logger.info(f"Updating EQL for layer '{layer_name}'")

    # Normalize layer name
    layer_name = _normalize_layer_name(client, layer_name, log=log)

    # Get current configuration
    current_config = get_layer_configuration(client, layer_name, log=False)

    # Update only specified fields
    if eql_query is not None:
        current_config.eql = eql_query
        if log:
            logger.debug(f"Setting EQL query: {eql_query[:100]}..." if len(eql_query) > 100 else f"Setting EQL query: {eql_query}")

    if eql_parameters is not None:
        current_config.eqlParameters = _convert_eql_parameters(eql_parameters)
        if log:
            logger.debug(f"Setting EQL parameters: {eql_parameters}")

    if condition is not None:
        current_config.condition = condition
        if log:
            logger.debug(f"Setting condition: {condition}")

    # Remove None values
    config_dict = _remove_none_values(current_config.model_dump())
    updated_config = QueryLayerServiceConfigurationDc(**config_dict)

    try:
        response = client.layers.patch_query_layer_service(
            name=layer_name,
            body=updated_config
        )
        if log:
            logger.info(f"Layer '{layer_name}' EQL updated successfully")
        return response
    except Exception as e:
        if log:
            logger.error(f"Error updating EQL for layer '{layer_name}': {e}")
        raise


def update_layer_style(
    client: Client,
    layer_name: str,
    client_style: Dict[str, Any],
    log: bool = True,
) -> Any:
    """Update layer Mapbox GL style.

    Updates only the clientStyle field without affecting other configuration.

    Args:
        client: EverGIS API client
        layer_name: Layer name (with or without username prefix)
        client_style: Mapbox GL style specification dict
        log: Enable logging

    Returns:
        API response with updated layer info

    Raises:
        ApiClientError: If layer doesn't exist or update fails

    Example:
        >>> # Simple circle style
        >>> style = {
        ...     "items": [{
        ...         "type": "circle",
        ...         "paint": {
        ...             "circle-color": "#ff0000",
        ...             "circle-radius": 5
        ...         }
        ...     }]
        ... }
        >>> update_layer_style(client, "my_layer", style)
        >>>
        >>> # Conditional coloring based on attribute
        >>> style = {
        ...     "items": [{
        ...         "type": "circle",
        ...         "paint": {
        ...             "circle-color": [
        ...                 "match", ["get", "status"],
        ...                 "active", "#00ff00",
        ...                 "inactive", "#ff0000",
        ...                 "#888888"  # default
        ...             ],
        ...             "circle-radius": 5,
        ...             "circle-stroke-color": "#ffffff",
        ...             "circle-stroke-width": 2
        ...         }
        ...     }]
        ... }
        >>> update_layer_style(client, "my_layer", style)
    """
    if log:
        logger.info(f"Updating style for layer '{layer_name}'")

    # Normalize layer name
    layer_name = _normalize_layer_name(client, layer_name, log=log)

    # Get current configuration
    current_config = get_layer_configuration(client, layer_name, log=False)

    # Update style
    current_config.clientStyle = client_style

    # Remove None values
    config_dict = _remove_none_values(current_config.model_dump())
    updated_config = QueryLayerServiceConfigurationDc(**config_dict)

    try:
        response = client.layers.patch_query_layer_service(
            name=layer_name,
            body=updated_config
        )
        if log:
            logger.info(f"Layer '{layer_name}' style updated successfully")
        return response
    except Exception as e:
        if log:
            logger.error(f"Error updating style for layer '{layer_name}': {e}")
        raise


def update_layer_attributes(
    client: Client,
    layer_name: str,
    attributes_configuration: AttributesConfigurationDc,
    log: bool = True,
) -> Any:
    """Update layer attributes configuration.

    Updates attribute metadata including aliases, types, editability,
    display settings, and string formatting.

    Args:
        client: EverGIS API client
        layer_name: Layer name (with or without username prefix)
        attributes_configuration: New attributes configuration
        log: Enable logging

    Returns:
        API response with updated layer info

    Raises:
        ApiClientError: If layer doesn't exist or update fails

    Example:
        >>> # Get current config and modify attributes
        >>> config = get_layer_configuration(client, "my_layer")
        >>> attrs = config.attributesConfiguration
        >>>
        >>> # Modify an attribute
        >>> for attr in attrs.attributes:
        ...     if attr.attributeName == "status":
        ...         attr.alias = "Status Field"
        ...         attr.isEditable = False
        ...
        >>> update_layer_attributes(client, "my_layer", attrs)
    """
    if log:
        logger.info(f"Updating attributes for layer '{layer_name}'")

    layer_name = _normalize_layer_name(client, layer_name, log=log)

    current_config = get_layer_configuration(client, layer_name, log=False)
    current_config.attributesConfiguration = attributes_configuration

    # Direct PATCH with ``serialize_as_any=True`` so subclass-only fields
    # (e.g. ``AttachmentsAttribute.subType``) survive serialization through
    # the un-discriminated ``attributes`` Union. The generated
    # ``patch_query_layer_service`` serializes with ``exclude_unset=True``
    # only and drops them on the wire.
    payload = current_config.model_dump(
        by_alias=True,
        exclude_none=True,
        mode="json",
        serialize_as_any=True,
    )
    try:
        response = client._request("patch", f"/layers/{layer_name}", json=payload)
        if log:
            attr_count = len(attributes_configuration.attributes) if attributes_configuration.attributes else 0
            logger.info(f"Layer '{layer_name}' attributes updated successfully ({attr_count} attributes)")
        return response
    except Exception as e:
        if log:
            logger.error(f"Error updating attributes for layer '{layer_name}': {e}")
        raise


def add_layer_attribute(
    client: Client,
    layer_name: str,
    attribute: AttributeConfigurationDc,
    log: bool = True,
) -> Any:
    """Append a single attribute to a layer's schema.

    Reads the current ``attributesConfiguration``, appends ``attribute``,
    and calls :func:`update_layer_attributes` to persist. The server now
    creates the backing physical column on its own from the PATCH /layers
    call - no separate ``PATCH /tables`` step is needed.

    Works for plain :class:`AttributeConfigurationDc` instances and for
    subtype-aware subclasses like :class:`AttachmentsAttribute` - the
    refreshed ``update_layer_attributes`` preserves subclass-only fields
    such as ``subType``.

    Args:
        client: EverGIS API client.
        layer_name: Layer name (with or without username prefix).
        attribute: ``AttributeConfigurationDc`` (or a subclass) to add.
        log: Enable logging.

    Returns:
        Response from the underlying ``PATCH /layers`` call.

    Raises:
        ValueError: If the layer already has an attribute with this name.

    Example:
        >>> from evergis_api.schemas import AttributeConfigurationDc
        >>> from evergis_tools.layers import add_layer_attribute
        >>>
        >>> add_layer_attribute(
        ...     client, "john_doe.my_layer",
        ...     AttributeConfigurationDc(
        ...         attributeName="note", columnName="note",
        ...         type="String", alias="Inspector note",
        ...     ),
        ... )
        >>>
        >>> # Attachments attribute - the same call, subType is preserved.
        >>> from evergis_tools.attribute_types import AttachmentsAttribute
        >>> add_layer_attribute(
        ...     client, "john_doe.my_layer",
        ...     AttachmentsAttribute(attributeName="docs", alias="Documents"),
        ... )
    """
    layer_name = _normalize_layer_name(client, layer_name, log=log)
    cfg = get_layer_configuration(client, layer_name, log=False)
    ac = cfg.attributesConfiguration
    if any(a.attributeName == attribute.attributeName for a in ac.attributes):
        raise ValueError(
            f"Layer '{layer_name}' already has an attribute "
            f"named '{attribute.attributeName}'"
        )
    ac.attributes.append(attribute)
    return update_layer_attributes(client, layer_name, ac, log=log)


def delete_layer_attribute(
    client: Client,
    layer_name: str,
    attribute_name: str,
    log: bool = True,
) -> Any:
    """Remove a single attribute from a layer's schema.

    Symmetric to :func:`add_layer_attribute`. Reads the current
    ``attributesConfiguration``, drops the entry whose
    ``attributeName`` matches, and calls :func:`update_layer_attributes`
    to persist. The server drops the backing physical column on its
    own from the PATCH /layers call - no separate ``PATCH /tables``
    step is needed.

    The protected ``idAttribute`` (``gid`` for gpkg-imported layers)
    cannot be removed; the geometry attribute can technically be
    removed but the layer will lose its render configuration - do it
    only when you know what you're doing.

    Args:
        client: EverGIS API client.
        layer_name: Layer name (with or without username prefix).
        attribute_name: Name of the attribute to remove.
        log: Enable logging.

    Returns:
        Response from the underlying ``PATCH /layers`` call.

    Raises:
        ValueError: If no attribute with that name exists on the layer,
            or if the caller tries to delete the ``idAttribute``.

    Example:
        >>> from evergis_tools.layers import delete_layer_attribute
        >>> delete_layer_attribute(client, "john_doe.my_layer", "note")
    """
    layer_name = _normalize_layer_name(client, layer_name, log=log)
    cfg = get_layer_configuration(client, layer_name, log=False)
    ac = cfg.attributesConfiguration

    id_attr = getattr(ac, "idAttribute", None)
    if id_attr and attribute_name == id_attr:
        raise ValueError(
            f"Cannot delete the layer's idAttribute ({attribute_name!r}) - "
            "it backs the primary key and feature ids."
        )

    before = len(ac.attributes)
    ac.attributes = [a for a in ac.attributes if a.attributeName != attribute_name]
    if len(ac.attributes) == before:
        raise ValueError(
            f"Layer '{layer_name}' has no attribute named '{attribute_name}'"
        )
    return update_layer_attributes(client, layer_name, ac, log=log)


def update_layer_attribute(
    client: Client,
    layer_name: str,
    attribute: AttributeConfigurationDc,
    log: bool = True,
) -> Any:
    """Replace a single attribute in a layer's schema by name.

    Reads the current ``attributesConfiguration``, finds the entry
    whose ``attributeName`` matches ``attribute.attributeName``,
    replaces it **whole** with the supplied object, and persists
    via :func:`update_layer_attributes`.

    Use this to:

    * tweak metadata (alias / description / stringFormat / isEditable / ...);
    * promote a plain attribute to a typed one (Default → Calculated
      via :class:`evergis_tools.attribute_types.CalculatedAttribute`,
      String → Attachments via
      :class:`evergis_tools.attribute_types.AttachmentsAttribute`);
    * change ``type`` / ``columnName`` / discriminator fields that
      ``update_layer_attributes`` would otherwise have to manage
      element-by-element.

    Because the new ``attribute`` is dropped in verbatim, **omit
    nothing you want to keep** - fields you don't set fall back to
    the class defaults (often ``None``), not to the previous values.
    Read the current attribute first if you want a partial change:

    .. code-block:: python

        cfg = get_layer_configuration(client, "john_doe.my_layer", log=False)
        attr = next(a for a in cfg.attributesConfiguration.attributes
                    if a.attributeName == "density")
        attr.alias = "Population density"
        attr.stringFormat = AttributeFormatConfigurationDc(format="#,#.00")
        update_layer_attribute(client, "john_doe.my_layer", attr)

    Args:
        client: EverGIS API client.
        layer_name: Layer name (with or without username prefix).
        attribute: ``AttributeConfigurationDc`` (or any subclass -
            ``CalculatedAttribute`` / ``StringAttributeConfigurationDc`` /
            ``AttachmentsAttribute`` / ``GeometryAttributeConfigurationDc``)
            whose ``attributeName`` identifies the slot to replace.
        log: Enable logging.

    Returns:
        Response from the underlying ``PATCH /layers`` call.

    Raises:
        ValueError: If no attribute with that name exists on the layer,
            or if the caller tries to replace the ``idAttribute`` with
            a differently-named one.

    Example:
        >>> from evergis_tools.attribute_types import CalculatedAttribute
        >>> from evergis_tools.layers import update_layer_attribute
        >>>
        >>> # Promote plain Double 'density' to a calculated value.
        >>> update_layer_attribute(client, "john_doe.my_layer",
        ...     CalculatedAttribute(
        ...         attributeName="density", columnName="density",
        ...         type="Double",
        ...         expression="population / NULLIF(area_km2, 0)",
        ...         alias="Population density",
        ...     ),
        ... )
    """
    layer_name = _normalize_layer_name(client, layer_name, log=log)
    cfg = get_layer_configuration(client, layer_name, log=False)
    ac = cfg.attributesConfiguration

    id_attr = getattr(ac, "idAttribute", None)
    if id_attr and id_attr in {a.attributeName for a in ac.attributes} \
            and id_attr != attribute.attributeName:
        # Caller is replacing some other attribute - that's fine.
        pass

    replaced = False
    for i, a in enumerate(ac.attributes):
        if a.attributeName == attribute.attributeName:
            ac.attributes[i] = attribute
            replaced = True
            break
    if not replaced:
        raise ValueError(
            f"Layer '{layer_name}' has no attribute named "
            f"'{attribute.attributeName}' - use add_layer_attribute "
            f"to create it instead."
        )
    return update_layer_attributes(client, layer_name, ac, log=log)


def update_layer_card(
    client: Client,
    layer_name: str,
    card_configuration: Dict[str, Any],
    log: bool = True,
) -> Any:
    """Update layer card (popup) configuration.

    Updates the card displayed when clicking on a feature.
    Card configuration defines the layout, components, and data sources
    for the feature popup.

    Args:
        client: EverGIS API client
        layer_name: Layer name (with or without username prefix)
        card_configuration: Card configuration dict with header, children, filters, dataSources
        log: Enable logging

    Returns:
        API response with updated layer info

    Raises:
        ApiClientError: If layer doesn't exist or update fails

    Example:
        >>> card = {
        ...     "header": {
        ...         "templateName": "Icon",
        ...         "options": {"bgColor": "#f0f0f0"},
        ...         "children": [
        ...             {"id": "title", "type": "attributeValue", "attributeName": "name"},
        ...             {"id": "description", "type": "attributeValue", "attributeName": "address"}
        ...         ]
        ...     },
        ...     "children": [{
        ...         "id": "pages",
        ...         "templateName": "Pages",
        ...         "children": [{
        ...             "id": "page1",
        ...             "templateName": "ContainersGroup",
        ...             "children": [{
        ...                 "id": "info",
        ...                 "templateName": "TwoColumn",
        ...                 "options": {"attributes": ["status", "created_date"]},
        ...                 "children": [
        ...                     {"id": "alias", "type": "attributeAlias"},
        ...                     {"id": "value", "type": "attributeValue"}
        ...                 ]
        ...             }]
        ...         }]
        ...     }],
        ...     "dataSources": []
        ... }
        >>> update_layer_card(client, "my_layer", card)
    """
    if log:
        logger.info(f"Updating card configuration for layer '{layer_name}'")

    # Normalize layer name
    layer_name = _normalize_layer_name(client, layer_name, log=log)

    # Get current configuration
    current_config = get_layer_configuration(client, layer_name, log=False)

    # Update card configuration
    current_config.cardConfiguration = card_configuration

    # Remove None values
    config_dict = _remove_none_values(current_config.model_dump())
    updated_config = QueryLayerServiceConfigurationDc(**config_dict)

    try:
        response = client.layers.patch_query_layer_service(
            name=layer_name,
            body=updated_config
        )
        if log:
            logger.info(f"Layer '{layer_name}' card configuration updated successfully")
        return response
    except Exception as e:
        if log:
            logger.error(f"Error updating card configuration for layer '{layer_name}': {e}")
        raise


def update_layer_edit_config(
    client: Client,
    layer_name: str,
    edit_configuration: Dict[str, Any],
    log: bool = True,
) -> Any:
    """Update layer edit form configuration.

    Updates the edit form displayed when editing a feature.
    Edit configuration defines the layout and controls (dropdowns, text inputs, etc.)
    for the feature edit form.

    Args:
        client: EverGIS API client
        layer_name: Layer name (with or without username prefix)
        edit_configuration: Edit form configuration with controls
        log: Enable logging

    Returns:
        API response with updated layer info

    Raises:
        ApiClientError: If layer doesn't exist or update fails

    Example:
        >>> edit_config = {
        ...     "children": [{
        ...         "id": "pages",
        ...         "templateName": "Pages",
        ...         "children": [{
        ...             "id": "page1",
        ...             "templateName": "ContainersGroup",
        ...             "children": [
        ...                 {
        ...                     "id": "status_edit",
        ...                     "templateName": "Edit",
        ...                     "children": [
        ...                         {"id": "alias", "type": "attributeAlias", "attributeName": "status"},
        ...                         {
        ...                             "id": "value",
        ...                             "type": "control",
        ...                             "attributeName": "status",
        ...                             "options": {
        ...                                 "control": {
        ...                                     "type": "dropdown",
        ...                                     "targetAttributeName": "status"
        ...                                 },
        ...                                 "relatedDataSource": "Statuses Lookup"
        ...                             }
        ...                         }
        ...                     ]
        ...                 }
        ...             ]
        ...         }]
        ...     }]
        ... }
        >>> update_layer_edit_config(client, "my_layer", edit_config)
    """
    if log:
        logger.info(f"Updating edit configuration for layer '{layer_name}'")

    # Normalize layer name
    layer_name = _normalize_layer_name(client, layer_name, log=log)

    # Get current configuration
    current_config = get_layer_configuration(client, layer_name, log=False)

    # Update edit configuration
    current_config.editConfiguration = edit_configuration

    # Remove None values
    config_dict = _remove_none_values(current_config.model_dump())
    updated_config = QueryLayerServiceConfigurationDc(**config_dict)

    try:
        response = client.layers.patch_query_layer_service(
            name=layer_name,
            body=updated_config
        )
        if log:
            logger.info(f"Layer '{layer_name}' edit configuration updated successfully")
        return response
    except Exception as e:
        if log:
            logger.error(f"Error updating edit configuration for layer '{layer_name}': {e}")
        raise
