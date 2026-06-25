# -*- coding: utf-8 -*-
"""Layer management utilities for EverGIS.

This module provides functions for creating, reading, and updating
EverGIS layer configurations.

Functions are organized into three categories:
- Create: gdf_to_layer, create_layer_from_schema, create_query_layer
- Read: get_layer_schema, get_layer_configuration, create_identity_mapping_from_layer
- Update: update_layer_configuration, update_layer_eql, update_layer_style,
          update_layer_attributes, update_layer_card, update_layer_edit_config

Example:
    >>> from evergis_api import Client
    >>> from evergis_tools.layers import (
    ...     create_query_layer,
    ...     get_layer_configuration,
    ...     update_layer_eql,
    ...     update_layer_style,
    ... )
    >>>
    >>> client = Client(base_url="...", sb_token="...")
    >>>
    >>> # Create a layer
    >>> create_query_layer(
    ...     client, "my_layer",
    ...     "SELECT * FROM table",
    ...     geometry_type="Point"
    ... )
    >>>
    >>> # Get configuration
    >>> config = get_layer_configuration(client, "my_layer")
    >>>
    >>> # Update EQL parameters
    >>> update_layer_eql(client, "my_layer", eql_parameters={"@filter": "value"})
    >>>
    >>> # Update style
    >>> update_layer_style(client, "my_layer", {"items": [...]})
"""

from .create import (
    gdf_to_layer,
    create_layer_from_schema,
    create_query_layer,
)
from .read import (
    get_layer_schema,
    get_layer_configuration,
    create_identity_mapping_from_layer,
    create_export_mappings_from_layer,
)
from .update import (
    update_layer_configuration,
    update_layer_eql,
    update_layer_style,
    update_layer_attributes,
    add_layer_attribute,
    delete_layer_attribute,
    update_layer_attribute,
    update_layer_card,
    update_layer_edit_config,
)
# Re-export type alias for backwards compatibility
from ._utils import OverwriteMode, declare_eql_parameter

__all__ = [
    # Create
    "gdf_to_layer",
    "create_layer_from_schema",
    "create_query_layer",
    # Read
    "get_layer_schema",
    "get_layer_configuration",
    "create_identity_mapping_from_layer",
    "create_export_mappings_from_layer",
    # Update
    "update_layer_configuration",
    "update_layer_eql",
    "update_layer_style",
    "update_layer_attributes",
    "add_layer_attribute",
    "delete_layer_attribute",
    "update_layer_attribute",
    "update_layer_card",
    "update_layer_edit_config",
    # Types
    "OverwriteMode",
    # EQL parameter declarations
    "declare_eql_parameter",
]
