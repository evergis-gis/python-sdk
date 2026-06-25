# -*- coding: utf-8 -*-
"""Functions for reprojecting geometries."""

import shapely.geometry


def shapely_reproject(
    geometry: shapely.geometry.base.BaseGeometry, 
    source_srid: int, 
    target_srid: int
) -> shapely.geometry.base.BaseGeometry:
    """Reproject a Shapely geometry to another coordinate reference system.

    Args:
        geometry: Shapely geometry
        source_srid: Source SRID
        target_srid: Target SRID

    Returns:
        Reprojected geometry
    """
    from shapely.ops import transform
    from pyproj import Transformer
    
    transformer = Transformer.from_crs(source_srid, target_srid, always_xy=True)
    return transform(transformer.transform, geometry)
