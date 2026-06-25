# -*- coding: utf-8 -*-
"""Utilities for working with Pydantic models and EverGIS layers.

This module provides generic utilities for:
- Extracting field information from Pydantic models
- Validating layer definitions against Pydantic schemas
- Creating attribute mappings between JSON and Pydantic models
- Finding models by name
"""

from typing import Type, Dict, Any, Tuple, List, Optional, Union, get_origin, get_args
from pydantic import BaseModel

# Import for type conversion
try:
    from .attributes import pydantic_to_attribute_type
except ImportError:
    # Fallback if attributes module not available
    def pydantic_to_attribute_type(python_type: Any, field_name: str = "") -> str:
        """Fallback implementation."""
        return "STRING"


def get_model_field_info(model_class: Type[BaseModel]) -> Dict[str, Dict[str, Any]]:
    """
    Extract field information from Pydantic model.

    Args:
        model_class: Pydantic model class (e.g., House, Street, Bridge)

    Returns:
        Dictionary mapping alias -> field info:
        {
            "CityId": {
                "python_name": "city_id",
                "type": "str",
                "is_optional": True,
                "field": FieldInfo(...)
            },
            ...
        }

    Example:
        >>> from pydantic import BaseModel, Field
        >>> class MyModel(BaseModel):
        ...     city_id: Optional[str] = Field(None, alias="CityId")
        >>> info = get_model_field_info(MyModel)
        >>> info["CityId"]["python_name"]
        'city_id'
    """
    field_info = {}

    for field_name, field in model_class.model_fields.items():
        alias = field.alias or field_name

        field_type = str(field.annotation)
        if hasattr(field.annotation, "__origin__"):
            field_type = str(field.annotation.__origin__.__name__)
        elif hasattr(field.annotation, "__name__"):
            field_type = field.annotation.__name__

        origin = get_origin(field.annotation)
        is_optional = origin is Union and type(None) in get_args(field.annotation)

        field_info[alias] = {
            "python_name": field_name,
            "type": field_type,
            "is_optional": is_optional,
            "field": field
        }

    return field_info


def validate_layer_against_model(
    json_layer_def: Dict[str, Any],
    model_class: Type[BaseModel]
) -> Dict[str, Any]:
    """
    Validate JSON layer definition against Pydantic model.

    Args:
        json_layer_def: Layer definition from EverGIS API
        model_class: Pydantic model class to validate against

    Returns:
        Validation report with:
        - matched_fields: Fields present in both JSON and model
        - missing_in_model: JSON fields not in model
        - missing_in_json: Model fields not in JSON
        - field_count: Statistics

    Example:
        >>> json_def = {
        ...     "attributes": {"CityId": {...}, "Name": {...}},
        ...     "geometryAttribute": "geometry"
        ... }
        >>> report = validate_layer_against_model(json_def, MyModel)
        >>> report["field_count"]["matched"]
        2
    """
    model_fields = get_model_field_info(model_class)
    json_attributes = json_layer_def.get("attributes", {})

    matched_fields = []
    missing_in_model = []

    for json_field_name in json_attributes.keys():
        if json_field_name == json_layer_def.get("geometryAttribute", "geometry"):
            continue

        if json_field_name in model_fields:
            matched_fields.append(json_field_name)
        else:
            missing_in_model.append(json_field_name)

    missing_in_json = [
        alias for alias in model_fields.keys()
        if alias not in json_attributes
    ]

    return {
        "matched_fields": matched_fields,
        "missing_in_model": missing_in_model,
        "missing_in_json": missing_in_json,
        "field_count": {
            "matched": len(matched_fields),
            "missing_in_model": len(missing_in_model),
            "missing_in_json": len(missing_in_json),
            "total_json": len([k for k in json_attributes.keys() if k != json_layer_def.get("geometryAttribute", "geometry")]),
            "total_model": len(model_fields)
        }
    }


def create_attribute_mappings(
    json_layer_def: Dict[str, Any],
    model_class: Type[BaseModel],
    exclude_geometry: bool = False
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Create attribute mappings using types from Pydantic model (not JSON).

    Maps fields present in BOTH JSON and Pydantic model, taking field types
    from the Pydantic model instead of JSON definition. This is essential for
    CSV imports where all fields come as String in JSON but should have proper
    types from the model.

    Args:
        json_layer_def: Layer definition from EverGIS API
        model_class: Pydantic model class
        exclude_geometry: Exclude geometry attribute from mappings (default: False)

    Returns:
        Tuple of (attribute_type_mapping, attribute_name_mapping)

        attribute_type_mapping: {"python_field": "EverGISType", ...}
        Types are taken from Pydantic model, not JSON!
        Example: {"quantity": "INT64", "name": "STRING"}  # from Pydantic types

        attribute_name_mapping: {"JSONField": "python_field", ...}
        Example: {"quantity": "quantity", "name": "name"}

    Example:
        >>> # CSV import where all fields are String in JSON
        >>> json_def = {
        ...     "attributes": {
        ...         "quantity": {"type": "String"},  # Wrong type in CSV
        ...         "name": {"type": "String"}
        ...     }
        ... }
        >>> class MyModel(BaseModel):
        ...     quantity: int  # Correct type
        ...     name: str
        >>> type_map, name_map = create_attribute_mappings(json_def, MyModel)
        >>> type_map["quantity"]
        'INT64'  # From Pydantic model, not JSON!
    """
    model_fields = get_model_field_info(model_class)
    json_attributes = json_layer_def.get("attributes", {})
    geometry_attr = json_layer_def.get("geometryAttribute", "geometry")

    attribute_type_mapping = {}
    attribute_name_mapping = {}

    for json_field_name, json_field_def in json_attributes.items():
        if json_field_name == geometry_attr:
            if not exclude_geometry:
                geometry_type = json_field_def.get("type")
                if geometry_type:
                    attribute_type_mapping["geometry"] = geometry_type
                    attribute_name_mapping["geometry"] = "geometry"
            continue

        if json_field_name in model_fields:
            model_field_info = model_fields[json_field_name]
            python_name = model_field_info["python_name"]

            # Get type from Pydantic model field, not from JSON
            field_annotation = model_class.model_fields[python_name].annotation
            evergis_type = pydantic_to_attribute_type(field_annotation, python_name)

            # Convert AttributeType enum to string if needed
            if hasattr(evergis_type, 'value'):
                evergis_type = evergis_type.value
            elif hasattr(evergis_type, 'name'):
                evergis_type = evergis_type.name

            attribute_type_mapping[python_name] = evergis_type
            attribute_name_mapping[json_field_name] = python_name

    return attribute_type_mapping, attribute_name_mapping


def get_matching_fields(
    json_layer_def: Dict[str, Any],
    model_class: Type[BaseModel],
    exclude_geometry: bool = False
) -> List[str]:
    """
    Get list of JSON field names that exist in the model.

    Args:
        json_layer_def: Layer definition from EverGIS API
        model_class: Pydantic model class
        exclude_geometry: Exclude geometry attribute from list (default: False)

    Returns:
        List of JSON field names (aliases) that match model fields

    Example:
        >>> matching = get_matching_fields(json_def, MyModel)
        >>> "CityId" in matching
        True
    """
    model_fields = get_model_field_info(model_class)
    json_attributes = json_layer_def.get("attributes", {})
    geometry_attr = json_layer_def.get("geometryAttribute", "geometry")

    matching_fields = []

    for json_field_name in json_attributes.keys():
        if json_field_name == geometry_attr:
            if not exclude_geometry:
                matching_fields.append(json_field_name)
            continue

        if json_field_name in model_fields:
            matching_fields.append(json_field_name)

    return matching_fields


def create_mappings_from_pydantic(
    model_class: Type[BaseModel],
    exclude_geometry: bool = False
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Create attribute mappings directly from Pydantic model schema.

    This function creates mappings using ONLY the Pydantic model, without
    needing a JSON layer definition from the API. Useful when you want to
    create a new layer based on a Pydantic schema.

    Args:
        model_class: Pydantic model class
        exclude_geometry: Exclude geometry attribute from mappings (default: False)

    Returns:
        Tuple of (attribute_type_mapping, attribute_name_mapping)

        attribute_type_mapping: {"python_field": "EverGISType", ...}
        Example: {"city_id": "STRING", "population": "INT64"}

        attribute_name_mapping: {"alias": "python_field", ...}
        Example: {"CityId": "city_id", "Population": "population"}

    Example:
        >>> from pydantic import BaseModel, Field
        >>> from typing import Optional
        >>>
        >>> class City(BaseModel):
        ...     city_id: str = Field(alias="CityId")
        ...     population: Optional[int] = Field(None, alias="Population")
        ...     name: str
        >>>
        >>> type_map, name_map = create_mappings_from_pydantic(City)
        >>> type_map
        {'city_id': 'STRING', 'population': 'INT64', 'name': 'STRING'}
        >>> name_map
        {'CityId': 'city_id', 'Population': 'population', 'name': 'name'}
    """
    attribute_type_mapping = {}
    attribute_name_mapping = {}

    for python_name, field in model_class.model_fields.items():
        # Skip geometry if requested
        if exclude_geometry and python_name == "geometry":
            continue

        # Get alias (or field name if no alias)
        alias = field.alias or python_name

        # Get EverGIS type from Pydantic field annotation
        field_annotation = field.annotation
        evergis_type = pydantic_to_attribute_type(field_annotation, python_name)

        # Convert AttributeType enum to string if needed
        if hasattr(evergis_type, 'value'):
            evergis_type = evergis_type.value
        elif hasattr(evergis_type, 'name'):
            evergis_type = evergis_type.name

        attribute_type_mapping[python_name] = evergis_type
        attribute_name_mapping[alias] = python_name

    return attribute_type_mapping, attribute_name_mapping


def create_mappings_from_json(
    json_data: Dict[str, Any],
    model_class: Type[BaseModel],
    layer_name: Optional[str] = None,
    exclude_geometry: bool = False
) -> Tuple[Dict[str, str], Dict[str, str]]:
    """
    Create mappings directly from EverGIS API JSON response.

    Args:
        json_data: Full JSON response from EverGIS API with layers array
        model_class: Pydantic model class to validate against
        layer_name: Specific layer name to process (if None, uses first layer)
        exclude_geometry: Exclude geometry attribute from mappings (default: False)

    Returns:
        Tuple of (attribute_type_mapping, attribute_name_mapping)

    Raises:
        ValueError: If layer not found or response invalid

    Example:
        >>> json_response = {
        ...     "layers": [{
        ...         "name": "cities",
        ...         "layerDefinition": {
        ...             "attributes": {"CityId": {"type": "String"}}
        ...         }
        ...     }]
        ... }
        >>> type_map, name_map = create_mappings_from_json(json_response, MyModel)
    """
    layers = json_data.get("layers", [])

    if not layers:
        raise ValueError("No layers found in response")

    if layer_name:
        layer = next((lyr for lyr in layers if lyr.get("name") == layer_name), None)
        if not layer:
            raise ValueError(f"Layer '{layer_name}' not found")
    else:
        layer = layers[0]

    layer_def = layer.get("layerDefinition")
    if not layer_def:
        raise ValueError("Layer definition not found")

    return create_attribute_mappings(
        layer_def,
        model_class,
        exclude_geometry=exclude_geometry
    )


def get_model_by_name(
    model_name: str,
    model_classes: List[Type[BaseModel]]
) -> Optional[Type[BaseModel]]:
    """
    Get Pydantic model class by name from provided list.

    Performs case-insensitive search by class name.

    Args:
        model_name: Model name (case-insensitive)
        model_classes: List of Pydantic model classes to search in

    Returns:
        Model class if found, None otherwise

    Example:
        >>> from myapp.schemas import House, Street, Bridge
        >>> model = get_model_by_name("house", [House, Street, Bridge])
        >>> model
        <class 'House'>
        >>> model = get_model_by_name("Street", [House, Street, Bridge])
        >>> model
        <class 'Street'>
        >>> model = get_model_by_name("unknown", [House, Street, Bridge])
        >>> model is None
        True
    """
    model_registry = {cls.__name__.lower(): cls for cls in model_classes}
    return model_registry.get(model_name.lower())


def create_mappings_from_json_auto(
    json_data: Dict[str, Any],
    model_classes: List[Type[BaseModel]],
    layer_index: int = 0,
    exclude_geometry: bool = False
) -> Tuple[Optional[Type[BaseModel]], Dict[str, str], Dict[str, str]]:
    """
    Automatically find model by layer name and create mappings.

    Args:
        json_data: Full JSON response from EverGIS API with layers array
        model_classes: List of Pydantic model classes to search in
        layer_index: Index of layer to process (default: 0)
        exclude_geometry: Exclude geometry attribute from mappings (default: False)

    Returns:
        Tuple of (model_class, attribute_type_mapping, attribute_name_mapping)
        model_class will be None if no matching model found

    Raises:
        ValueError: If layer not found or response invalid

    Example:
        >>> from myapp.schemas import House, Street
        >>> json_data = {"layers": [{"name": "Houses", ...}]}
        >>> model, type_map, name_map = create_mappings_from_json_auto(
        ...     json_data, [House, Street]
        ... )
        >>> model
        <class 'House'>
    """
    layers = json_data.get("layers", [])

    if not layers:
        raise ValueError("No layers found in response")

    if layer_index >= len(layers):
        raise ValueError(f"Layer index {layer_index} out of range (total layers: {len(layers)})")

    layer = layers[layer_index]
    layer_name = layer.get("name", "")

    model_class = get_model_by_name(layer_name, model_classes)

    if not model_class:
        return None, {}, {}

    layer_def = layer.get("layerDefinition")
    if not layer_def:
        raise ValueError("Layer definition not found")

    type_mapping, name_mapping = create_attribute_mappings(
        layer_def,
        model_class,
        exclude_geometry=exclude_geometry
    )

    return model_class, type_mapping, name_mapping
