# -*- coding: utf-8 -*-
"""Tests for geometry/reprojection.py -- coordinate transforms."""

from shapely.geometry import Point

from evergis_tools.geometry.reprojection import shapely_reproject


class TestShapelyReproject:
    """Tests for shapely_reproject()."""

    def test_4326_to_3857(self):
        point = Point(30.0, 10.0)
        result = shapely_reproject(point, 4326, 3857)
        assert result.geom_type == "Point"
        # Web Mercator coordinates are much larger
        assert abs(result.x) > 1_000_000
        assert abs(result.y) > 1_000_000

    def test_3857_to_4326(self):
        point = Point(3339584.7, 1118889.97)
        result = shapely_reproject(point, 3857, 4326)
        assert -180 <= result.x <= 180
        assert -90 <= result.y <= 90

    def test_roundtrip(self):
        original = Point(30.0, 10.0)
        projected = shapely_reproject(original, 4326, 3857)
        back = shapely_reproject(projected, 3857, 4326)
        assert abs(back.x - original.x) < 1e-6
        assert abs(back.y - original.y) < 1e-6
