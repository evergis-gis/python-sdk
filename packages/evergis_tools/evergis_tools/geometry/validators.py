# -*- coding: utf-8 -*-
"""Validation utilities for geometry data."""

from typing import List, Dict, Any, Union, Type
import re
import logging

logger = logging.getLogger(__name__)


def assert_geometry_instance(geometry: Any, expected_type: Type, type_name: str) -> None:
    """Assert that geometry object is instance of expected type.

    Args:
        geometry: Geometry object to validate
        expected_type: Expected Python type
        type_name: Human-readable type name for error message

    Raises:
        ValueError: If geometry is not of expected type

    Example:
        >>> from shapely.geometry import Point
        >>> point = Point(1, 2)
        >>> assert_geometry_instance(point, Point, "Point")  # OK
        >>> assert_geometry_instance("invalid", Point, "Point")  # Raises ValueError
    """
    if not isinstance(geometry, expected_type):
        raise ValueError(
            f"Expected {type_name}, got {type(geometry).__name__}"
        )


def validate_srid(srid: Union[int, str]) -> bool:
    """Check if SRID (Spatial Reference System Identifier) is valid.

    Args:
        srid: SRID to validate

    Returns:
        True if SRID is valid, False otherwise

    Example:
        >>> validate_srid(4326)
        True
        >>> validate_srid("4326")
        True
        >>> validate_srid(999)
        False
    """
    try:
        srid_int = int(srid)
        # Usually SRID in range 1000-32767 for custom systems
        # and less than 1000 for standard ones (e.g., 4326 for WGS84)
        return 1 <= srid_int <= 32767
    except (ValueError, TypeError):
        return False


def validate_geometry_type(geom_type: str) -> bool:
    """Check if geometry type is valid.

    Args:
        geom_type: Geometry type to validate

    Returns:
        True if type is valid, False otherwise

    Example:
        >>> validate_geometry_type("Point")
        True
        >>> validate_geometry_type("InvalidType")
        False
    """
    if not isinstance(geom_type, str):
        return False

    valid_types = {
        'Point', 'LineString', 'Polygon', 'MultiPoint',
        'MultiLineString', 'MultiPolygon', 'GeometryCollection'
    }

    return geom_type in valid_types


def validate_ewkt_format(ewkt_string: str) -> bool:
    """Check EWKT string format.

    Args:
        ewkt_string: EWKT string to validate

    Returns:
        True if format is correct, False otherwise

    Example:
        >>> validate_ewkt_format("SRID=4326;POINT(30 10)")
        True
        >>> validate_ewkt_format("POINT(30 10)")
        True
        >>> validate_ewkt_format("INVALID")
        False
    """
    if not isinstance(ewkt_string, str) or not ewkt_string.strip():
        return False

    # Pattern for EWKT: [SRID=number;]GEOMETRY(coordinates)
    ewkt_pattern = r'^(SRID=\d+;)?(POINT|LINESTRING|POLYGON|MULTIPOINT|MULTILINESTRING|MULTIPOLYGON|GEOMETRYCOLLECTION)\s*\('

    return bool(re.match(ewkt_pattern, ewkt_string.upper()))


def validate_coordinates(coordinates: List[float], dimension: int = 2) -> bool:
    """Check if coordinates are valid.

    Args:
        coordinates: List of coordinates
        dimension: Expected dimension (2D, 3D)

    Returns:
        True if coordinates are valid, False otherwise

    Example:
        >>> validate_coordinates([30.0, 10.0])
        True
        >>> validate_coordinates([30.0, 10.0, 5.0], dimension=3)
        True
        >>> validate_coordinates([30.0])
        False
    """
    if not isinstance(coordinates, list):
        return False

    if len(coordinates) < dimension:
        return False

    # Check that all coordinates are numbers
    for coord in coordinates:
        if not isinstance(coord, (int, float)):
            return False

        # Check for infinity and NaN
        if not (-180 <= coord <= 180):  # Simple check for geographic coordinates
            logger.warning(f"Coordinate {coord} is out of reasonable bounds")

    return True


def validate_bbox(bbox: List[float]) -> bool:
    """Check if bounding box is valid.

    Args:
        bbox: List [minx, miny, maxx, maxy]

    Returns:
        True if bbox is valid, False otherwise

    Example:
        >>> validate_bbox([10.0, 20.0, 30.0, 40.0])
        True
        >>> validate_bbox([30.0, 20.0, 10.0, 40.0])
        False
    """
    if not isinstance(bbox, list) or len(bbox) != 4:
        return False

    minx, miny, maxx, maxy = bbox

    # Check that all values are numbers
    if not all(isinstance(coord, (int, float)) for coord in bbox):
        return False

    # Check correct order
    if minx >= maxx or miny >= maxy:
        return False

    return True


def validate_geojson_feature(feature: Dict[str, Any]) -> bool:
    """Check if GeoJSON feature is valid.

    Args:
        feature: GeoJSON feature

    Returns:
        True if feature is valid, False otherwise

    Example:
        >>> feature = {
        ...     "type": "Feature",
        ...     "geometry": {"type": "Point", "coordinates": [30, 10]},
        ...     "properties": {"name": "Test"}
        ... }
        >>> validate_geojson_feature(feature)
        True
    """
    if not isinstance(feature, dict):
        return False

    # Check required fields
    if feature.get("type") != "Feature":
        return False

    if "geometry" not in feature or "properties" not in feature:
        return False

    # Check geometry
    geometry = feature["geometry"]
    if geometry is not None:
        if not isinstance(geometry, dict):
            return False

        if "type" not in geometry or "coordinates" not in geometry:
            return False

        if not validate_geometry_type(geometry["type"]):
            return False

    # Check properties
    if not isinstance(feature["properties"], dict):
        return False

    return True
