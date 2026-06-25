# -*- coding: utf-8 -*-
"""Shared fixtures for evergis_tools tests."""

import pytest
import geopandas as gpd
from shapely.geometry import (
    Point,
    LineString,
    Polygon,
    MultiPoint,
    MultiLineString,
    MultiPolygon,
    GeometryCollection,
)
from unittest.mock import MagicMock

from evergis_api.schemas import (
    PointDc,
    LineStringDc,
    PolygonDc,
    EnvelopeDc,
    FeatureDc,
    PagedFeaturesListDc,
)


# =====================================================================
# Shapely geometry fixtures
# =====================================================================


@pytest.fixture
def shapely_point():
    return Point(30.0, 10.0)


@pytest.fixture
def shapely_linestring():
    return LineString([(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)])


@pytest.fixture
def shapely_polygon():
    return Polygon([(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)])


@pytest.fixture
def shapely_multipoint():
    return MultiPoint([(0.0, 0.0), (1.0, 1.0)])


@pytest.fixture
def shapely_multilinestring():
    return MultiLineString([[(0.0, 0.0), (1.0, 1.0)], [(2.0, 2.0), (3.0, 3.0)]])


@pytest.fixture
def shapely_multipolygon():
    return MultiPolygon([
        Polygon([(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]),
        Polygon([(2, 2), (3, 2), (3, 3), (2, 3), (2, 2)]),
    ])


@pytest.fixture
def shapely_geometry_collection():
    return GeometryCollection([Point(0, 0), LineString([(0, 0), (1, 1)])])


# =====================================================================
# EverGIS Dc geometry fixtures
# =====================================================================


@pytest.fixture
def point_dc():
    return PointDc(type="Point", coordinates=(30.0, 10.0), srId=4326)


@pytest.fixture
def linestring_dc():
    return LineStringDc(
        type="LineString",
        coordinates=[(0.0, 0.0), (1.0, 1.0), (2.0, 0.0)],
        srId=4326,
    )


@pytest.fixture
def polygon_dc():
    return PolygonDc(
        type="Polygon",
        coordinates=[[(0.0, 0.0), (1.0, 0.0), (1.0, 1.0), (0.0, 1.0), (0.0, 0.0)]],
        srId=4326,
    )


@pytest.fixture
def envelope_dc():
    return EnvelopeDc(coordinates=[(0.0, 0.0), (1.0, 1.0)], srId=4326)


# =====================================================================
# GeoDataFrame fixtures
# =====================================================================


@pytest.fixture
def simple_point_gdf():
    """GeoDataFrame with points and attributes."""
    return gpd.GeoDataFrame(
        {"name": ["A", "B", "C"], "value": [1, 2, 3]},
        geometry=[Point(30.0, 10.0), Point(31.0, 11.0), Point(32.0, 12.0)],
        crs="EPSG:4326",
    )


@pytest.fixture
def mixed_geom_gdf():
    """GeoDataFrame with mixed geometry types."""
    return gpd.GeoDataFrame(
        {"id": [1, 2, 3]},
        geometry=[
            Point(0, 0),
            LineString([(0, 0), (1, 1)]),
            Polygon([(0, 0), (1, 0), (1, 1), (0, 0)]),
        ],
        crs="EPSG:4326",
    )


@pytest.fixture
def empty_gdf():
    """Empty GeoDataFrame."""
    return gpd.GeoDataFrame(columns=["geometry", "name"], crs="EPSG:4326")


@pytest.fixture
def gdf_with_nulls():
    """GeoDataFrame with null geometries and attributes."""
    return gpd.GeoDataFrame(
        {"name": ["A", None, "C"], "value": [1, float("nan"), 3]},
        geometry=[Point(0, 0), None, Point(1, 1)],
        crs="EPSG:4326",
    )


# =====================================================================
# FeatureDc / PagedFeaturesListDc fixtures
# =====================================================================


@pytest.fixture
def sample_feature_dc():
    return FeatureDc(
        properties={"name": "Test", "value": 42},
        geometry=PointDc(type="Point", coordinates=(30.0, 10.0), srId=4326),
    )


@pytest.fixture
def sample_paged_features():
    features = [
        FeatureDc(
            properties={"name": "A"},
            geometry=PointDc(type="Point", coordinates=(30.0, 10.0), srId=4326),
        ),
        FeatureDc(
            properties={"name": "B"},
            geometry=PointDc(type="Point", coordinates=(31.0, 11.0), srId=4326),
        ),
    ]
    return PagedFeaturesListDc(features=features, totalCount=2, limit=10, offset=0)


# =====================================================================
# Mock client fixture
# =====================================================================


@pytest.fixture
def mock_client():
    """Mock EverGIS API Client."""
    client = MagicMock()
    client.remotetaskmanager = MagicMock()
    return client
