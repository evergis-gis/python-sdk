# -*- coding: utf-8 -*-
"""EverGIS Tools - utilities for working with EverGIS API.

High-level utilities built on top of evergis_api for:
- Attribute handling and type conversions
- Catalog and resource management
- Configuration constants and mappings
- Data export utilities (GeoJSON, CSV)
- Data validation utilities
- EQL query utilities
- Feature operations
- Field name utilities (safe naming, transliteration)
- GeoDataFrame integration
- Geospatial analysis tools (Voronoi, routing, isochrones)
- Geometry conversion and processing
- Layer and table operations
- Logging configuration
- Pydantic schema utilities (validation, mapping, field extraction)
- Task execution system

See module docstrings for detailed documentation.
"""

from ._utils import to_safe_field_name
from ._errors import (
    ApiTransientError,
    ResourceExists,
    ResourceNotFound,
    is_conflict,
    is_not_found,
    is_transient,
)
from .client import AsyncClient, Client
from .layers import (
    # Create
    create_layer_from_schema,
    gdf_to_layer,
    create_query_layer,
    # Read
    get_layer_schema,
    get_layer_configuration,
    create_identity_mapping_from_layer,
    create_export_mappings_from_layer,
    # Update
    update_layer_configuration,
    update_layer_eql,
    update_layer_style,
    update_layer_attributes,
    update_layer_card,
    update_layer_edit_config,
    # Types
    OverwriteMode,
)
from .attributes import pydantic_to_attribute_type, validate_gdf_fields_by_layer
from .attribute_types import (
    Attachment,
    AttachmentsAttribute,
    attachment_from_file,
    attachment_from_resource,
    attachment_from_url,
    attachments_from_json,
    attachments_to_json,
)
from .pydantic_utils import (
    get_model_field_info,
    validate_layer_against_model,
    create_attribute_mappings,
    create_mappings_from_pydantic,
    get_matching_fields,
    create_mappings_from_json,
    get_model_by_name,
    create_mappings_from_json_auto,
)

__version__ = "0.2.0"

__all__ = [
    "to_safe_field_name",
    # Typed errors and predicates
    "ApiTransientError",
    "ResourceExists",
    "ResourceNotFound",
    "is_conflict",
    "is_not_found",
    "is_transient",
    # Layers - Create
    "create_layer_from_schema",
    "gdf_to_layer",
    "create_query_layer",
    # Layers - Read
    "get_layer_schema",
    "get_layer_configuration",
    "create_identity_mapping_from_layer",
    "create_export_mappings_from_layer",
    # Layers - Update
    "update_layer_configuration",
    "update_layer_eql",
    "update_layer_style",
    "update_layer_attributes",
    "update_layer_card",
    "update_layer_edit_config",
    # Layers - Types
    "OverwriteMode",
    # Attributes
    "pydantic_to_attribute_type",
    "validate_gdf_fields_by_layer",
    # Attachments attribute type
    "Attachment",
    "AttachmentsAttribute",
    "attachment_from_file",
    "attachment_from_resource",
    "attachment_from_url",
    "attachments_from_json",
    "attachments_to_json",
    # Pydantic utilities
    "get_model_field_info",
    "validate_layer_against_model",
    "create_attribute_mappings",
    "create_mappings_from_pydantic",
    "get_matching_fields",
    "create_mappings_from_json",
    "get_model_by_name",
    "create_mappings_from_json_auto",
]
