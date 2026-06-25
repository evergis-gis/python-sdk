# -*- coding: utf-8 -*-
"""General validation utilities for data."""

from typing import Any, List, Dict
import logging


logger = logging.getLogger(__name__)


def validate_feature_properties(properties: Dict[str, Any],
                               required_fields: List[str] = None) -> bool:
    """Check if feature properties are valid.

    Args:
        properties: Feature properties dictionary
        required_fields: List of required fields

    Returns:
        True if properties are valid, False otherwise

    Example:
        >>> props = {"id": 1, "name": "Feature1"}
        >>> validate_feature_properties(props, ["id"])
        True
        >>> validate_feature_properties(props, ["id", "missing"])
        False
    """
    if not isinstance(properties, dict):
        return False

    # Check required fields
    if required_fields:
        for field in required_fields:
            if field not in properties:
                return False

            # Check that value is not None and not empty string
            value = properties[field]
            if value is None or (isinstance(value, str) and not value.strip()):
                return False

    return True


def validate_pagination_params(page: int = None, limit: int = None) -> bool:
    """Check if pagination parameters are valid.

    Args:
        page: Page number
        limit: Page size

    Returns:
        True if parameters are valid, False otherwise

    Example:
        >>> validate_pagination_params(1, 100)
        True
        >>> validate_pagination_params(0, 100)
        False
        >>> validate_pagination_params(1, 20000)
        False
    """
    if page is not None:
        if not isinstance(page, int) or page < 1:
            return False

    if limit is not None:
        if not isinstance(limit, int) or limit < 1 or limit > 10000:  # Reasonable limits
            return False

    return True


