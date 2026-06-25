# -*- coding: utf-8 -*-
"""Module for working with Voronoi diagrams."""

import logging
import numpy as np
import geopandas as gpd
from shapely.geometry import Point, Polygon, MultiPolygon
from scipy.spatial import Voronoi
from typing import Optional, Union, List

logger = logging.getLogger(__name__)


def create_voronoi_cells(
    points_gdf: gpd.GeoDataFrame,
    boundary: Optional[Union[Polygon, MultiPolygon]] = None,
    buffer_distance: float = 0.0,
    crs: Optional[str] = None,
    return_original_points: bool = False
) -> gpd.GeoDataFrame:
    """
    Build Voronoi cells from the points in a GeoDataFrame.

    Args:
        points_gdf: GeoDataFrame with points for building the Voronoi diagram
        boundary: Boundary polygon for clipping the cells (optional)
        buffer_distance: Buffer distance for expanding the boundary (in CRS units)
        crs: Coordinate system for the result (if None, the input CRS is used)
        return_original_points: Whether to return the original points along with the cells

    Returns:
        GeoDataFrame with Voronoi cells

    Raises:
        ValueError: If points_gdf has no points or they are not Point geometries
        ValueError: If boundary is not a Polygon or MultiPolygon
    """

    # Validate the input data
    if points_gdf.empty:
        raise ValueError("The GeoDataFrame with points must not be empty")

    if not all(isinstance(geom, Point) for geom in points_gdf.geometry):
        raise ValueError("All geometries in points_gdf must be points (Point)")

    if boundary is not None and not isinstance(boundary, (Polygon, MultiPolygon)):
        raise ValueError("boundary must be a Polygon or MultiPolygon")

    # Determine the CRS
    if crs is None:
        crs = points_gdf.crs

    # Extract point coordinates
    points = []
    for point in points_gdf.geometry:
        points.append([point.x, point.y])

    points = np.array(points)

    if len(points) < 3:
        raise ValueError("At least 3 points are required to build a Voronoi diagram")

    # Build the Voronoi diagram
    try:
        vor = Voronoi(points)
    except Exception as e:
        logger.error(f"Error while building the Voronoi diagram: {e}")
        raise

    # Build the Voronoi cells
    cells = []
    cell_data = []

    for point_idx, region_idx in enumerate(vor.point_region):
        if region_idx == -1:
            # The point lies on the convex hull boundary
            logger.warning(f"Point {point_idx} lies on the convex hull boundary")
            continue

        region = vor.regions[region_idx]

        if len(region) < 3:
            # The region is too small
            logger.warning(f"Region {region_idx} has fewer than 3 vertices")
            continue

        # Build a polygon from the region vertices, excluding infinite edges
        vertices = []
        for vertex_idx in region:
            if vertex_idx != -1:  # Exclude infinite vertices
                vertices.append(vor.vertices[vertex_idx])

        if len(vertices) < 3:
            logger.warning(f"Region {region_idx} has fewer than 3 finite vertices")
            continue

        try:
            polygon = Polygon(vertices)
            if polygon.is_valid and not polygon.is_empty:
                cells.append(polygon)
                cell_data.append({
                    'point_index': point_idx,
                    'region_index': region_idx,
                    'area': polygon.area,
                    'centroid_x': polygon.centroid.x,
                    'centroid_y': polygon.centroid.y
                })
            else:
                # Don't drop it silently - leave a trace at debug level.
                logger.debug(f"Region {region_idx}: invalid/empty polygon - skipped")
        except Exception as e:
            logger.warning(f"Could not build a polygon for region {region_idx}: {e}")
            continue

    if not cells:
        raise ValueError("Could not build any Voronoi cells")

    # Build a GeoDataFrame with the cells
    cells_gdf = gpd.GeoDataFrame(
        cell_data,
        geometry=cells,
        crs=crs
    )

    # Apply the boundary polygon if provided
    if boundary is not None:
        cells_gdf = _clip_cells_to_boundary(cells_gdf, boundary, buffer_distance)

    # Add the original points if requested
    if return_original_points:
        cells_gdf = _add_original_points(cells_gdf, points_gdf)

    return cells_gdf


def _clip_cells_to_boundary(
    cells_gdf: gpd.GeoDataFrame,
    boundary: Union[Polygon, MultiPolygon],
    buffer_distance: float = 0.0
) -> gpd.GeoDataFrame:
    """
    Clip Voronoi cells to a boundary polygon.

    Args:
        cells_gdf: GeoDataFrame with Voronoi cells
        boundary: Boundary polygon
        buffer_distance: Buffer distance

    Returns:
        GeoDataFrame with clipped cells
    """

    # Apply a buffer to the boundary if specified
    if buffer_distance > 0:
        boundary = boundary.buffer(buffer_distance)

    # Clip the cells to the boundary
    clipped_cells = []
    clipped_data = []

    for idx, row in cells_gdf.iterrows():
        cell = row.geometry
        try:
            clipped = cell.intersection(boundary)
            if clipped.is_valid and not clipped.is_empty:
                clipped_cells.append(clipped)
                # Update the data
                data = row.to_dict()
                data['area'] = clipped.area
                data['centroid_x'] = clipped.centroid.x
                data['centroid_y'] = clipped.centroid.y
                clipped_data.append(data)
            else:
                # Empty intersection = cell lies outside the boundary; a
                # normal geometric outcome, but trace it instead of dropping
                # silently.
                logger.debug(f"Cell {idx}: empty intersection with the boundary - skipped")
        except Exception as e:
            logger.warning(f"Error while clipping cell {idx}: {e}")
            continue

    if not clipped_cells:
        raise ValueError("No cells remained after clipping")
    
    return gpd.GeoDataFrame(
        clipped_data,
        geometry=clipped_cells,
        crs=cells_gdf.crs
    )


def _add_original_points(
    cells_gdf: gpd.GeoDataFrame,
    points_gdf: gpd.GeoDataFrame
) -> gpd.GeoDataFrame:
    """
    Add the original points to the Voronoi cells.

    Args:
        cells_gdf: GeoDataFrame with Voronoi cells
        points_gdf: GeoDataFrame with the original points

    Returns:
        GeoDataFrame with cells and points
    """

    # Create a copy of the cells
    result_gdf = cells_gdf.copy()

    # Add the points
    for idx, row in cells_gdf.iterrows():
        point_idx = row['point_index']
        if point_idx < len(points_gdf):
            point_row = points_gdf.iloc[point_idx]
            # Add the point data to the cell
            for col in points_gdf.columns:
                if col != 'geometry':
                    result_gdf.at[idx, f'point_{col}'] = point_row[col]

    return result_gdf


def create_voronoi_with_attributes(
    points_gdf: gpd.GeoDataFrame,
    attribute_columns: List[str],
    boundary: Optional[Union[Polygon, MultiPolygon]] = None,
    buffer_distance: float = 0.0,
    crs: Optional[str] = None
) -> gpd.GeoDataFrame:
    """
    Build Voronoi cells while preserving the attributes of the original points.

    Args:
        points_gdf: GeoDataFrame with points
        attribute_columns: List of attribute columns to preserve
        boundary: Boundary polygon (optional)
        buffer_distance: Buffer distance
        crs: Coordinate system

    Returns:
        GeoDataFrame with Voronoi cells and point attributes
    """

    # Check that the specified columns exist
    missing_columns = [col for col in attribute_columns if col not in points_gdf.columns]
    if missing_columns:
        raise ValueError(f"Columns not found in points_gdf: {missing_columns}")

    # Build the Voronoi cells with the original points
    cells_gdf = create_voronoi_cells(
        points_gdf=points_gdf,
        boundary=boundary,
        buffer_distance=buffer_distance,
        crs=crs,
        return_original_points=True
    )

    # Rename the attribute columns
    for col in attribute_columns:
        if f'point_{col}' in cells_gdf.columns:
            cells_gdf = cells_gdf.rename(columns={f'point_{col}': col})

    return cells_gdf

