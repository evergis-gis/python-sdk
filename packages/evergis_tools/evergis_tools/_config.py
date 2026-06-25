# -*- coding: utf-8 -*-
"""Configuration constants and mappings for EverGIS API Utils."""

# ============================================================================
# Geometry Type Mappings
# ============================================================================

# Shapely geometry types to EverGIS AttributeType mapping
# Used by attributes.py to determine geometry column type for layer schemas
SHAPELY_TO_EVERGIS_GEOMETRY_MAPPING = {
    'Point': 'POINT',
    'MultiPoint': 'MULTIPOINT',
    'LineString': 'LINESTRING',
    'MultiLineString': 'MULTILINESTRING',
    'Polygon': 'POLYGON',
    'MultiPolygon': 'MULTIPOLYGON',
}

# ============================================================================
# Pandas Type Mappings
# ============================================================================

# Pandas dtype check functions to AttributeType mapping (string names)
def _get_pandas_to_evergis_mapping():
    """Return mapping of pandas type check functions to EverGIS types."""
    try:
        import pandas as pd
        return {
            pd.api.types.is_integer_dtype: 'INT32',
            pd.api.types.is_float_dtype: 'DOUBLE',
            pd.api.types.is_datetime64_any_dtype: 'DATETIME',
            pd.api.types.is_bool_dtype: 'BOOLEAN',
        }
    except ImportError:
        return {}

# Default type for unrecognized pandas dtypes
DEFAULT_PANDAS_TYPE = 'STRING'

# ============================================================================
# Attribute Cleaning Constants
# ============================================================================

# String values that represent null/None/NaN
NULL_STRING_VALUES = frozenset(['nan', 'null', 'none', ''])

# ============================================================================
# Field Type Detection
# ============================================================================

# Datetime format patterns for field type detection
DATETIME_PATTERNS = (
    r'^\d{4}-\d{2}-\d{2}$',  # YYYY-MM-DD
    r'^\d{4}-\d{2}-\d{2} \d{2}:\d{2}:\d{2}$',  # YYYY-MM-DD HH:MM:SS
    r'^\d{4}-\d{2}-\d{2}T\d{2}:\d{2}:\d{2}',  # ISO 8601
    r'^\d{2}\.\d{2}\.\d{4}$',  # DD.MM.YYYY
    r'^\d{2}/\d{2}/\d{4}$',  # DD/MM/YYYY
    r'^\d{2}-\d{2}-\d{4}$',  # DD-MM-YYYY
)

# ============================================================================
# Field Name Management
# ============================================================================

# Default field name when result is empty after cleaning
DEFAULT_FIELD_NAME = 'field'

# Cyrillic to Latin transliteration mapping
CYRILLIC_TO_LATIN_MAP = {
    'а': 'a', 'б': 'b', 'в': 'v', 'г': 'g', 'д': 'd', 'е': 'e', 'ё': 'yo',
    'ж': 'zh', 'з': 'z', 'и': 'i', 'й': 'y', 'к': 'k', 'л': 'l', 'м': 'm',
    'н': 'n', 'о': 'o', 'п': 'p', 'р': 'r', 'с': 's', 'т': 't', 'у': 'u',
    'ф': 'f', 'х': 'h', 'ц': 'ts', 'ч': 'ch', 'ш': 'sh', 'щ': 'sch',
    'ъ': '', 'ы': 'y', 'ь': '', 'э': 'e', 'ю': 'yu', 'я': 'ya',
    'А': 'A', 'Б': 'B', 'В': 'V', 'Г': 'G', 'Д': 'D', 'Е': 'E', 'Ё': 'Yo',
    'Ж': 'Zh', 'З': 'Z', 'И': 'I', 'Й': 'Y', 'К': 'K', 'Л': 'L', 'М': 'M',
    'Н': 'N', 'О': 'O', 'П': 'P', 'Р': 'R', 'С': 'S', 'Т': 'T', 'У': 'U',
    'Ф': 'F', 'Х': 'H', 'Ц': 'Ts', 'Ч': 'Ch', 'Ш': 'Sh', 'Щ': 'Sch',
    'Ъ': '', 'Ы': 'Y', 'Ь': '', 'Э': 'E', 'Ю': 'Yu', 'Я': 'Ya'
}
