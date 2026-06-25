# -*- coding: utf-8 -*-
"""EWKT (Extended Well-Known Text) conversion utilities.

This module provides functions for converting between Shapely geometries
and EWKT format (WKT with SRID prefix).
"""

from typing import Optional

from shapely import wkt


def ewkt_to_shapely(ewkt_string: str):
    """Convert EWKT string to Shapely geometry.

    Args:
        ewkt_string: EWKT string like 'SRID=4326;POINT(30 10)'

    Returns:
        Shapely geometry with srid attribute

    Raises:
        ImportError: If Shapely is not installed
        ValueError: If EWKT string is invalid

    Example:
        >>> geom = ewkt_to_shapely("SRID=4326;POINT(30 10)")
        >>> print(geom.x, geom.y)  # 30.0 10.0
        >>> print(geom.srid)       # 4326
    """
    if not ewkt_string or not isinstance(ewkt_string, str):
        raise ValueError("EWKT string must be a non-empty string")

    try:
        # Extract SRID prefix if present
        if 'SRID=' in ewkt_string:
            srid_part, geom_wkt = ewkt_string.split(';', 1)
            srid_value = int(srid_part.replace('SRID=', ''))
        else:
            geom_wkt = ewkt_string
            srid_value = None

        # Parse WKT to Shapely geometry
        geometry = wkt.loads(geom_wkt)

        # Add SRID as attribute
        if srid_value:
            geometry.srid = srid_value

        return geometry

    except Exception as e:
        raise ValueError(f"Failed to parse EWKT '{ewkt_string}': {e}") from e


def shapely_to_ewkt(geometry, srid: Optional[int] = None) -> str:
    """Convert Shapely geometry to EWKT string.

    Args:
        geometry: Shapely geometry
        srid: SRID to add (optional)

    Returns:
        EWKT string

    Raises:
        ImportError: If Shapely is not installed

    Example:
        >>> from shapely.geometry import Point
        >>> point = Point(30, 10)
        >>> ewkt = shapely_to_ewkt(point, srid=4326)
        >>> print(ewkt)  # "SRID=4326;POINT (30 10)"
    """
    # Get WKT representation
    wkt_string = geometry.wkt

    # Use SRID from geometry or passed parameter
    geometry_srid = getattr(geometry, 'srid', None) or srid

    if geometry_srid:
        return f"SRID={geometry_srid};{wkt_string}"

    return wkt_string


__all__ = [
    'ewkt_to_shapely',
    'shapely_to_ewkt',
]
