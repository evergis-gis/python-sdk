# -*- coding: utf-8 -*-
"""Geometry conversion and utilities for EverGIS."""

from .shapely import (
    shapely_to_evergis_geometry,
    evergis_geometry_to_shapely,
    evergis_dict_to_shapely,
)

from .reprojection import (
    shapely_reproject,
)

from .ewkt import (
    ewkt_to_shapely,
    shapely_to_ewkt,
)

from .validators import (
    assert_geometry_instance,
    validate_srid,
    validate_geometry_type,
    validate_ewkt_format,
    validate_coordinates,
    validate_bbox,
    validate_geojson_feature,
)

__all__ = [
    # Shapely <-> EverGIS
    'shapely_to_evergis_geometry',
    'evergis_geometry_to_shapely',
    'evergis_dict_to_shapely',

    # Reprojection
    'shapely_reproject',

    # EWKT
    'ewkt_to_shapely',
    'shapely_to_ewkt',

    # Validators
    'assert_geometry_instance',
    'validate_srid',
    'validate_geometry_type',
    'validate_ewkt_format',
    'validate_coordinates',
    'validate_bbox',
    'validate_geojson_feature',
]
