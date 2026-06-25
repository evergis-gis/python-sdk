# -*- coding: utf-8 -*-
"""GeoJSON-native geometry conversion between Shapely and EverGIS API."""

from typing import Dict, Any, Union
import logging

from shapely.geometry import shape as _shape, mapping as _mapping, box as _box
from shapely.geometry.base import BaseGeometry

from evergis_api.schemas import (
    PointDc,
    MultiLineStringDc,
    PolygonDc,
    MultiPointDc,
    LineStringDc,
    MultiPolygonDc,
    EnvelopeDc,
    GeometryCollectionDc,
)

logger = logging.getLogger(__name__)


# ============================================================================
# Shapely → EverGIS GeometryDc
# ============================================================================

_SHAPELY_TO_DC = {
    'Point': PointDc,
    'LineString': LineStringDc,
    'MultiLineString': MultiLineStringDc,
    'Polygon': PolygonDc,
    'MultiPolygon': MultiPolygonDc,
    'MultiPoint': MultiPointDc,
}


def shapely_to_evergis_geometry(
    geometry: BaseGeometry, sr_id: int
) -> Union[PointDc, LineStringDc, MultiLineStringDc, PolygonDc, MultiPointDc, MultiPolygonDc]:
    """Convert Shapely geometry to EverGIS GeometryDc using GeoJSON interop.

    Args:
        geometry: Shapely geometry of any supported type
        sr_id: Spatial reference ID

    Returns:
        Corresponding EverGIS GeometryDc object

    Raises:
        ValueError: If geometry type is not supported
    """
    dc_class = _SHAPELY_TO_DC.get(geometry.geom_type)
    if dc_class is None:
        raise ValueError(f"Unsupported geometry type: {geometry.geom_type}")

    geojson = _mapping(geometry)
    return dc_class(type=geojson['type'], coordinates=geojson['coordinates'], srId=sr_id)


# ============================================================================
# EverGIS GeometryDc → Shapely
# ============================================================================

def evergis_geometry_to_shapely(
    geometry_dc: Union[
        PointDc, MultiLineStringDc, PolygonDc, MultiPointDc,
        LineStringDc, MultiPolygonDc, EnvelopeDc, GeometryCollectionDc
    ]
) -> BaseGeometry:
    """Convert EverGIS GeometryDc to Shapely geometry using GeoJSON interop.

    Args:
        geometry_dc: EverGIS GeometryDc object (GeoJSON-compatible)

    Returns:
        Corresponding Shapely geometry

    Raises:
        ValueError: If GeometryDc type is not supported
    """
    # EnvelopeDc is not GeoJSON - handle separately
    if isinstance(geometry_dc, EnvelopeDc):
        if len(geometry_dc.coordinates) != 2:
            raise ValueError(
                f"EnvelopeDc must have exactly 2 coordinates, got {len(geometry_dc.coordinates)}"
            )
        min_x, min_y = geometry_dc.coordinates[0]
        max_x, max_y = geometry_dc.coordinates[1]
        return _box(min_x, min_y, max_x, max_y)

    # All other Dc types are GeoJSON-compatible
    return _shape(geometry_dc.model_dump(exclude={'srId'}))


# ============================================================================
# Dict → Shapely (backward compat for old API format)
# ============================================================================

# Old EverGIS type strings → GeoJSON type strings
_OLD_TO_GEOJSON_TYPE = {
    'point': 'Point',
    'polyline': 'MultiLineString',
    'polygon': 'Polygon',
    'multipolygon': 'MultiPolygon',
    'multipoint': 'MultiPoint',
    'linestring': 'LineString',
    'multilinestring': 'MultiLineString',
    'line': 'LineString',
}


def evergis_dict_to_shapely(evergis_dict: Dict[str, Any]) -> BaseGeometry:
    """Convert EverGIS geometry dict to Shapely object.

    Handles both old-format dicts (lowercase types like "polyline", "polygon")
    and new GeoJSON-format dicts ("Point", "MultiLineString", etc.).

    Args:
        evergis_dict: Dict with 'type' and 'coordinates' keys

    Returns:
        Shapely geometry object

    Raises:
        ValueError: If dict is invalid or type unsupported
    """
    if not isinstance(evergis_dict, dict):
        raise ValueError("EverGIS geometry must be a dict")
    if 'type' not in evergis_dict:
        raise ValueError("EverGIS geometry must contain 'type' field")
    if 'coordinates' not in evergis_dict:
        raise ValueError("EverGIS geometry must contain 'coordinates' field")

    raw_type = evergis_dict['type']
    geojson_type = _OLD_TO_GEOJSON_TYPE.get(raw_type.lower(), raw_type)

    return _shape({'type': geojson_type, 'coordinates': evergis_dict['coordinates']})


__all__ = [
    'shapely_to_evergis_geometry',
    'evergis_geometry_to_shapely',
    'evergis_dict_to_shapely',
]
