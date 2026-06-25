# -*- coding: utf-8 -*-
"""Internal utility functions for evergis_tools package.

This module contains private helper functions used internally by the package.
These functions are not part of the public API and should not be imported by external code.
"""

import re
import unicodedata
from typing import TypeVar, Any, Optional
from pydantic import BaseModel

T = TypeVar('T', bound=BaseModel)


def _remove_none_values(obj: T) -> T:
    """Remove fields with None values from Pydantic object and return new object of same type.

    Recursively processes nested Pydantic objects, lists, and dictionaries,
    removing all None values while preserving the structure.

    Args:
        obj: Pydantic model object

    Returns:
        New object of same type without fields with None values

    Example:
        >>> from pydantic import BaseModel
        >>> class User(BaseModel):
        ...     name: str
        ...     age: int | None = None
        >>> user = User(name="Alice", age=None)
        >>> cleaned = _remove_none_values(user)
        >>> cleaned.model_dump()
        {'name': 'Alice'}
    """
    def _clean_obj(obj_to_clean: Any) -> Any:
        """Recursively clean objects from None values."""
        if isinstance(obj_to_clean, BaseModel):
            # For Pydantic objects get dictionary without None values
            clean_dict = {}
            for field_name, field_value in obj_to_clean.model_dump().items():
                if field_value is not None:
                    clean_dict[field_name] = _clean_obj(field_value)
            # Create new object of same type
            return obj_to_clean.__class__(**clean_dict)
        elif isinstance(obj_to_clean, list):
            # For lists clean each element
            return [_clean_obj(item) for item in obj_to_clean if item is not None]
        elif isinstance(obj_to_clean, dict):
            # For dictionaries clean values
            return {k: _clean_obj(v) for k, v in obj_to_clean.items() if v is not None}
        else:
            # For simple types return as is
            return obj_to_clean

    return _clean_obj(obj)


def _to_snake_case(text: str) -> str:
    """Convert text to snake_case.

    Handles:
    - camelCase → snake_case
    - PascalCase → snake_case
    - Already snake_case (no change)
    - Consecutive capitals (HTTPResponse → http_response)

    Args:
        text: Text to convert

    Returns:
        Text in snake_case format

    Example:
        >>> _to_snake_case("fieldName")
        'field_name'
        >>> _to_snake_case("HTTPResponse")
        'http_response'
        >>> _to_snake_case("already_snake_case")
        'already_snake_case'
    """
    # Insert underscore before uppercase letters that follow lowercase
    text = re.sub('([a-z0-9])([A-Z])', r'\1_\2', text)

    # Insert underscore before uppercase letter followed by lowercase
    # (handles consecutive capitals: HTTPResponse → HTTP_Response)
    text = re.sub('([A-Z]+)([A-Z][a-z])', r'\1_\2', text)

    # Convert to lowercase
    return text.lower()


def _ensure_unique_field_name(name: str, existing_names: set, max_length: int = 16) -> str:
    """Ensure field name uniqueness with length constraint.

    Args:
        name: Desired field name
        existing_names: Set of already used names
        max_length: Maximum field name length

    Returns:
        Unique field name

    Example:
        >>> _ensure_unique_field_name("field", {"field"}, 16)
        'field_1'
        >>> _ensure_unique_field_name("very_long_field_name", set(), 10)
        'very_long_'
    """
    # Truncate to max length
    base_name = name[:max_length]

    if base_name not in existing_names:
        return base_name

    # Find unique name by adding numbers
    for i in range(1, 1000):
        # Calculate space for suffix
        suffix = f"_{i}"
        available_length = max_length - len(suffix)
        if available_length < 1:
            available_length = 1

        candidate = base_name[:available_length] + suffix
        if candidate not in existing_names:
            return candidate

    # If couldn't find unique name, return with timestamp
    import time
    timestamp = str(int(time.time()) % 10000)
    return f"field_{timestamp}"


def to_safe_field_name(
    name: str,
    *,
    max_length: Optional[int] = None,
    ensure_unique: bool = False,
    existing_names: Optional[set] = None,
    to_snake_case: bool = True,
    allow_numbers_start: bool = False
) -> str:
    """Convert field name to safe format.

    Process:
    1. Transliterate Cyrillic to Latin
    2. Remove diacritics (accents, umlauts)
    3. Convert to snake_case (if enabled)
    4. Remove/replace invalid characters
    5. Normalize underscores
    6. Ensure starts with letter (if required)
    7. Truncate to max_length (if specified)
    8. Ensure uniqueness (if requested)

    Args:
        name: Original field name
        max_length: Maximum length (None = unlimited)
        ensure_unique: Whether to ensure uniqueness
        existing_names: Set of existing names (required if ensure_unique=True)
        to_snake_case: Convert camelCase/PascalCase to snake_case
        allow_numbers_start: Allow field names starting with numbers

    Returns:
        Safe field name

    Raises:
        ValueError: If ensure_unique=True but existing_names not provided

    Example:
        >>> to_safe_field_name("Название Поля")
        'nazvanie_polya'
        >>> to_safe_field_name("fieldName", to_snake_case=True)
        'field_name'
        >>> to_safe_field_name("123field")
        'f_123field'
        >>> to_safe_field_name("Very-Long Field Name!", max_length=10)
        'very_long_'
        >>> existing = {"field_name"}
        >>> to_safe_field_name("fieldName", ensure_unique=True, existing_names=existing)
        'field_name_1'
    """
    from ._config import CYRILLIC_TO_LATIN_MAP, DEFAULT_FIELD_NAME

    if ensure_unique and existing_names is None:
        raise ValueError("existing_names must be provided when ensure_unique=True")

    if not isinstance(name, str):
        name = str(name)

    # Step 0: Normalize Unicode (compose multi-character sequences like и+breve → й)
    name = unicodedata.normalize('NFC', name)

    # Step 1: Transliterate Cyrillic to Latin
    result = ''.join(CYRILLIC_TO_LATIN_MAP.get(char, char) for char in name)

    # Step 2: Remove diacritical marks (accents, umlauts, etc.)
    result = unicodedata.normalize('NFD', result)
    result = ''.join(char for char in result if unicodedata.category(char) != 'Mn')

    # Convert superscript/subscript numbers to regular numbers (² → 2, ³ → 3, etc.)
    superscript_map = str.maketrans('⁰¹²³⁴⁵⁶⁷⁸⁹', '0123456789')
    subscript_map = str.maketrans('₀₁₂₃₄₅₆₇₈₉', '0123456789')
    result = result.translate(superscript_map).translate(subscript_map)

    # Step 3: Convert to snake_case if requested
    if to_snake_case:
        result = _to_snake_case(result)

    # Step 4: Replace spaces and special characters with underscores
    result = re.sub(r'[^\w]', '_', result)

    # Step 5: Normalize underscores - collapse multiple and strip
    result = re.sub(r'_+', '_', result)
    result = result.strip('_')

    # Use default if empty
    if not result:
        result = DEFAULT_FIELD_NAME

    # Step 6: Ensure starts with letter if required
    if not allow_numbers_start and result and not result[0].isalpha():
        result = 'f_' + result

    # Step 7: Truncate to max_length if specified
    if max_length is not None and len(result) > max_length:
        result = result[:max_length].rstrip('_')
        if not result:
            result = DEFAULT_FIELD_NAME[:max_length]

    # Step 8: Ensure uniqueness if requested
    if ensure_unique and existing_names is not None:
        # If no max_length specified for uniqueness, use a reasonable default
        unique_max_length = max_length if max_length is not None else 64
        result = _ensure_unique_field_name(result, existing_names, unique_max_length)

    return result
