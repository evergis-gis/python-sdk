# -*- coding: utf-8 -*-
"""Utilities for working with attributes, fields, and type conversions in EverGIS API."""

from typing import Any, Dict, Optional, Union, TYPE_CHECKING
import json
import logging
import re

if TYPE_CHECKING:
    import geopandas as gpd

from evergis_api.schemas import AttributeType, AttributesConfigurationDc

logger = logging.getLogger(__name__)


# ============================================================================
# Type Conversion (Private)
# ============================================================================


def _pandas_dtype_to_attribute_type(dtype: Any, column_name: str) -> AttributeType:
    """Convert pandas dtype to EverGIS AttributeType.

    Args:
        dtype: Pandas data type
        column_name: Column name (used for geometry detection)

    Returns:
        Corresponding AttributeType

    Example:
        >>> import pandas as pd
        >>> pandas_dtype_to_attribute_type(pd.Int64Dtype(), "count")
        <AttributeType.INT32: 'Int32'>
    """
    # Geometry is determined by column name
    if column_name == "geometry":
        return AttributeType.MULTIPOLYGON  # Default, can be overridden

    # Use mapping from _config.py
    from ._config import _get_pandas_to_evergis_mapping, DEFAULT_PANDAS_TYPE

    # Get mapping of check functions
    type_mapping = _get_pandas_to_evergis_mapping()

    # Check each function from mapping
    for check_func, evergis_type_name in type_mapping.items():
        if check_func(dtype):
            return getattr(AttributeType, evergis_type_name)

    # Default type
    return getattr(AttributeType, DEFAULT_PANDAS_TYPE)


def pydantic_to_attribute_type(python_type: Any, field_name: str = "") -> AttributeType:
    """Convert Python/Pydantic type annotation to EverGIS AttributeType.

    Args:
        python_type: Python type annotation from Pydantic field
        field_name: Field name (for logging purposes)

    Returns:
        Corresponding AttributeType

    Note:
        Plain ``int`` maps to ``Int32``, not ``Int64``. The server treats
        an ``Int64`` column as an autoincrement primary key (NOT NULL), so
        a regular ``Int64`` data column silently rejects NULLs and
        overwrites values. The layer's identifier (``id_attribute`` in
        ``create_layer_from_schema``) is the one column kept ``Int64``.
        Declare ``Field(json_schema_extra={"attribute_type": "Int64"})``
        when a non-PK column genuinely needs the 64-bit range.

    Example:
        >>> from typing import Optional
        >>> pydantic_to_attribute_type(int, "count")
        <AttributeType.INT32: 'Int32'>
        >>> pydantic_to_attribute_type(Optional[str], "name")
        <AttributeType.STRING: 'String'>
    """
    from datetime import datetime, date

    # Handle None type
    if python_type is type(None):
        return AttributeType.STRING

    # Unwrap Optional/Union types
    if hasattr(python_type, "__origin__"):
        origin = python_type.__origin__

        # Union types (including Optional which is Union[X, None])
        if origin is Union:
            args = getattr(python_type, "__args__", ())
            # Find first non-None type
            for arg in args:
                if arg is not type(None):
                    # Recursive call for inner type
                    return pydantic_to_attribute_type(arg, field_name)
            # All args are None?
            return AttributeType.STRING

        # List/dict → JSON
        if origin is list or origin is dict:
            return AttributeType.JSON

    # Direct type mapping
    type_map = {
        int: AttributeType.INT32,
        str: AttributeType.STRING,
        float: AttributeType.DOUBLE,
        bool: AttributeType.BOOLEAN,
        datetime: AttributeType.DATETIME,
        date: AttributeType.DATETIME,  # No separate DATE type, use DATETIME
        list: AttributeType.JSON,
        dict: AttributeType.JSON,
    }

    attr_type = type_map.get(python_type)
    if attr_type:
        return attr_type

    # Default fallback
    logger.debug(f"Unknown type {python_type} for field {field_name}, defaulting to STRING")
    return AttributeType.STRING


def _get_geometry_attribute_type(gdf: "gpd.GeoDataFrame") -> Optional[AttributeType]:
    """Determine geometry type in GeoDataFrame for AttributeType.

    Args:
        gdf: GeoDataFrame

    Returns:
        Corresponding AttributeType for geometry or None

    Example:
        >>> import geopandas as gpd
        >>> from shapely.geometry import Point
        >>> gdf = gpd.GeoDataFrame(geometry=[Point(0, 0)])
        >>> get_geometry_attribute_type(gdf)
        <AttributeType.POINT: 'Point'>
    """
    if gdf.empty or "geometry" not in gdf.columns:
        return None

    # Get geometry types from non-empty values
    valid_geoms = gdf.geometry.dropna()
    if valid_geoms.empty:
        return None

    geom_types = valid_geoms.geom_type.value_counts()
    most_common_type = geom_types.index[0]

    # Geometry-type breakdown - at debug so it doesn't spam INFO on every call.
    if logger.isEnabledFor(logging.DEBUG):
        logger.debug("Geometry types in data:")
        for geom_type, count in geom_types.items():
            logger.debug(f"  {geom_type}: {count} objects")
        logger.debug(f"Most common type: {most_common_type}")

    # Use mapping from _config.py
    from ._config import SHAPELY_TO_EVERGIS_GEOMETRY_MAPPING

    # Get string type name from config
    evergis_type_name = SHAPELY_TO_EVERGIS_GEOMETRY_MAPPING.get(most_common_type)

    if evergis_type_name is None:
        raise ValueError(
            f"Unknown geometry type: {most_common_type}. "
            f"Supported types: {list(SHAPELY_TO_EVERGIS_GEOMETRY_MAPPING.keys())}"
        )

    # Convert string to AttributeType
    return getattr(AttributeType, evergis_type_name)


def _detect_field_type(value: str) -> str:
    """Detect field type based on its value.

    Args:
        value: String field value

    Returns:
        Field type (Int32, Double, DateType, Json, String)

    Example:
        >>> _detect_field_type("123")
        'Int32'
        >>> _detect_field_type("3.14")
        'Double'
        >>> _detect_field_type("2024-01-01")
        'DateType'
    """
    if not value or value.strip() == "":
        return "String"

    value = value.strip()

    # Check types in order of specificity
    if _is_int32(value):
        return "Int32"

    if _is_double(value):
        return "Double"

    if _is_datetime(value):
        return "DateType"

    if _is_json(value):
        return "Json"

    return "String"


def _is_int32(value: str) -> bool:
    """Check if value can be parsed as Int32.

    Args:
        value: String value to check

    Returns:
        True if value is Int32, False otherwise
    """
    try:
        int(value)
        return True
    except ValueError:
        return False


def _is_double(value: str) -> bool:
    """Check if value can be parsed as Double (float).

    Args:
        value: String value to check

    Returns:
        True if value is Double, False otherwise
    """
    try:
        # Support both dot and comma as decimal separator
        test_value = value.replace(",", ".")
        float(test_value)
        # Only return True if it actually has decimal part
        return "." in value or "," in value
    except ValueError:
        return False


def _is_datetime(value: str) -> bool:
    """Check if value matches datetime patterns.

    Args:
        value: String value to check

    Returns:
        True if value matches datetime pattern, False otherwise
    """
    from ._config import DATETIME_PATTERNS

    return any(re.match(pattern, value) for pattern in DATETIME_PATTERNS)


def _is_json(value: str) -> bool:
    """Check if value is valid JSON.

    Args:
        value: String value to check

    Returns:
        True if value is valid JSON, False otherwise
    """
    if not value.startswith(("{", "[")):
        return False

    try:
        json.loads(value)
        return True
    except (json.JSONDecodeError, ValueError):
        return False


# ============================================================================
# Attribute Cleaning (Public)
# ============================================================================


def clean_attributes_for_evergis(attributes: Dict[str, Any]) -> Dict[str, Any]:
    """Clean attributes for compatibility with EverGIS API.

    Scalar types (String, Int32/Int64, Double, Boolean, DateTime) are passed
    through. Collections (list / dict / tuple) are unwrapped from numpy types
    and returned as native Python list/dict so they go on the wire as native
    JSON for the server's ``Json`` columns - stringified JSON is silently
    dropped by the server.

    Args:
        attributes: Original attributes

    Returns:
        Cleaned attributes

    Example:
        >>> clean_attributes_for_evergis({"count": None, "active": True, "tags": ["a", "b"]})
        {'count': None, 'active': True, 'tags': ['a', 'b']}
    """
    return {key: _clean_single_attribute(value) for key, value in attributes.items()}


def _clean_single_attribute(value: Any) -> Any:
    """Clean a single attribute value for EverGIS API compatibility.

    Args:
        value: Attribute value to clean

    Returns:
        Cleaned value (None, basic type, or JSON string)
    """
    # Check for null-like values first
    if _is_null_like(value):
        return None

    # Dispatch to type-specific handlers
    # Order matters: bool before int/float (bool is subclass of int)
    if isinstance(value, bool):
        return _clean_boolean(value)
    if isinstance(value, (int, float)):
        return _clean_numeric(value)
    if isinstance(value, str):
        return _clean_string(value)
    if isinstance(value, (list, dict, tuple)):
        return _clean_collection(value)

    # Fallback for other types
    return _clean_other(value)


def _is_null_like(value: Any) -> bool:
    """Check if value represents null/None/NaN.

    Args:
        value: Value to check

    Returns:
        True if value is null-like, False otherwise
    """
    from ._config import NULL_STRING_VALUES

    if value is None:
        return True

    # Check string representations of null
    if isinstance(value, str) and value.lower() in NULL_STRING_VALUES:
        return True

    # Check pandas NaN for numeric values
    if isinstance(value, (int, float)):
        try:
            import pandas as pd

            return pd.isna(value)
        except (ImportError, TypeError, ValueError):
            pass

    return False


def _clean_numeric(value: Union[int, float]) -> Optional[Union[int, float]]:
    """Clean numeric value, checking for NaN if pandas available.

    Args:
        value: Numeric value to clean

    Returns:
        Original value or None if NaN
    """
    try:
        import pandas as pd

        return None if pd.isna(value) else value
    except (ImportError, TypeError, ValueError):
        return value


def _clean_string(value: str) -> Optional[str]:
    """Clean string value.

    Args:
        value: String value to clean

    Returns:
        Original string or None if null-like
    """
    from ._config import NULL_STRING_VALUES

    return None if value.lower() in NULL_STRING_VALUES else value


def _clean_boolean(value: bool) -> bool:
    """Keep boolean value as-is.

    Args:
        value: Boolean value

    Returns:
        Original boolean value
    """
    return value


def _convert_numpy_to_python(obj: Any) -> Any:
    """Recursively convert numpy types to Python native types for JSON serialization.

    Args:
        obj: Object that may contain numpy types

    Returns:
        Object with numpy types converted to Python native types
    """
    try:
        import numpy as np
        has_numpy = True
    except ImportError:
        has_numpy = False

    if has_numpy:
        if isinstance(obj, np.ndarray):
            return [_convert_numpy_to_python(item) for item in obj.tolist()]
        elif isinstance(obj, (np.integer,)):
            return int(obj)
        elif isinstance(obj, (np.floating,)):
            return float(obj)
        elif isinstance(obj, (np.bool_,)):
            return bool(obj)

    if isinstance(obj, dict):
        return {k: _convert_numpy_to_python(v) for k, v in obj.items()}
    elif isinstance(obj, (list, tuple)):
        return [_convert_numpy_to_python(item) for item in obj]

    return obj


def _clean_collection(value: Union[list, dict, tuple]) -> Optional[Union[list, dict]]:
    """Return collection as a native Python list/dict (numpy types unwrapped).

    For EverGIS ``Json`` columns the value must reach the server as a native
    JSON object/array under ``properties.<column>``; a stringified JSON
    (``json.dumps(...)``) is silently dropped by the server. Tuples are
    normalised to lists since JSON has no tuple type.

    Args:
        value: Collection (list, dict, or tuple)

    Returns:
        Python list/dict ready for native JSON serialization, or None if empty.
    """
    if not value:
        return None
    return _convert_numpy_to_python(value)


def _clean_other(value: Any) -> Optional[str]:
    """Convert other types to string.

    Args:
        value: Value of unknown type

    Returns:
        String representation or None if empty

    Raises:
        ValueError: If conversion to string fails
    """
    from ._config import NULL_STRING_VALUES

    # Check if empty
    if hasattr(value, "__len__"):
        try:
            if len(value) == 0:
                return None
        except (TypeError, ValueError):
            pass

    # Convert to string
    try:
        str_value = str(value)
        return None if str_value.lower() in NULL_STRING_VALUES else str_value
    except (TypeError, ValueError) as exc:
        logger.exception("Error converting attribute value %r to string", value)
        raise ValueError(f"Failed to convert attribute value to string: {type(value)}") from exc


# ============================================================================
# Field Validation (Public)
# ============================================================================


def validate_gdf_fields_by_layer(
    gdf: "gpd.GeoDataFrame",
    layer_schema: AttributesConfigurationDc,
    check_types: bool = False,
    strict: bool = False,
    log: bool = True,
) -> tuple[bool, list[str]]:
    """Validate GeoDataFrame fields against layer schema.

    Checks that:
    - All GDF fields exist in layer schema
    - Optionally validates field types match

    Args:
        gdf: GeoDataFrame to validate
        layer_schema: Layer schema from get_layer_schema()
        check_types: If True, also validate field types match
        strict: If True, raise ValueError on validation failure; if False, only log warnings
        log: Enable logging

    Returns:
        Tuple of (is_valid, error_messages)
        - is_valid: True if validation passed, False otherwise
        - error_messages: List of validation error/warning messages

    Raises:
        ValueError: If strict=True and validation fails

    Example:
        >>> from evergis_tools import get_layer_schema, validate_gdf_fields_by_layer
        >>> import geopandas as gpd
        >>>
        >>> # Get layer schema
        >>> schema = get_layer_schema(client, "username.my_layer")
        >>>
        >>> # Validate GeoDataFrame fields
        >>> is_valid, errors = validate_gdf_fields_by_layer(
        ...     gdf=my_gdf,
        ...     layer_schema=schema,
        ...     check_types=True
        ... )
        >>> if not is_valid:
        ...     print("Validation warnings:", errors)
    """
    errors = []

    # Get GDF columns (excluding geometry)
    gdf_columns = set(col for col in gdf.columns if col != "geometry")

    # Check if layer schema has attributes
    if not layer_schema.attributes:
        if log:
            logger.warning("Layer schema has no attributes defined")
        return True, []

    # Build lookup dict: attributeName -> attribute config
    attrs_by_name = {
        attr.attributeName: attr for attr in layer_schema.attributes
    }
    layer_attrs = set(attrs_by_name.keys())

    # Required-fields check is gone: the API no longer exposes
    # per-attribute nullability (isNullable / isAutoincrement were
    # removed from AttributeConfigurationDc), so the client cannot
    # tell which fields are mandatory. The server validates on write.

    # 1. Check for extra fields not in schema
    extra_fields = gdf_columns - layer_attrs
    if extra_fields:
        errors.append(
            f"Extra fields not in layer schema (will be excluded): {sorted(extra_fields)}"
        )

    # 2. Check field types if requested
    if check_types:
        common_fields = gdf_columns & layer_attrs
        for field_name in common_fields:
            # Get GDF field type
            try:
                gdf_dtype = gdf[field_name].dtype
                gdf_attr_type = _pandas_dtype_to_attribute_type(gdf_dtype, field_name)
            except Exception as e:
                if log:
                    logger.debug(f"Could not determine type for field '{field_name}': {e}")
                continue

            # Get schema field type
            schema_attr_type = attrs_by_name[field_name].type

            # Compare types (allow some flexibility)
            if not _types_compatible(gdf_attr_type, schema_attr_type):
                errors.append(
                    f"Type mismatch for field '{field_name}': "
                    f"GDF has {gdf_attr_type.value}, schema expects {schema_attr_type.value}"
                )

    # Determine if validation passed
    is_valid = len(errors) == 0

    # Handle validation results
    if not is_valid:
        error_msg = "\n".join(f"  - {err}" for err in errors)
        full_msg = f"GeoDataFrame field validation issues:\n{error_msg}"

        if strict:
            raise ValueError(full_msg)

        if log:
            logger.warning(full_msg)

    elif log:
        logger.info(f"GeoDataFrame field validation passed: {len(gdf_columns)} fields validated")

    return is_valid, errors


def _types_compatible(gdf_type: AttributeType, schema_type: AttributeType) -> bool:
    """Check if GeoDataFrame field type is compatible with schema type.

    Allows some flexibility for numeric types (e.g., INT32 can be used for INT64).

    Args:
        gdf_type: AttributeType from GeoDataFrame
        schema_type: AttributeType from layer schema

    Returns:
        True if types are compatible, False otherwise
    """
    # Exact match is always OK
    if gdf_type == schema_type:
        return True

    # Define compatible type groups
    numeric_types = {AttributeType.INT32, AttributeType.INT64, AttributeType.DOUBLE}
    string_types = {AttributeType.STRING, AttributeType.JSON}
    geometry_types = {
        AttributeType.POINT,
        AttributeType.LINESTRING,
        AttributeType.POLYGON,
        AttributeType.MULTIPOINT,
        AttributeType.MULTILINESTRING,
        AttributeType.MULTIPOLYGON,
    }

    # Allow conversions within numeric types (with potential precision loss warning)
    if gdf_type in numeric_types and schema_type in numeric_types:
        return True

    # Allow string/JSON interchangeability
    if gdf_type in string_types and schema_type in string_types:
        return True

    # Allow geometry type flexibility (e.g., Polygon can go into MultiPolygon)
    if gdf_type in geometry_types and schema_type in geometry_types:
        return True

    return False
