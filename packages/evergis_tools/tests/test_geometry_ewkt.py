# -*- coding: utf-8 -*-
"""Tests for geometry/ewkt.py -- EWKT conversion."""

import pytest
from shapely.geometry import Point

from evergis_tools.geometry.ewkt import ewkt_to_shapely, shapely_to_ewkt


class TestEwktToShapely:
    """Tests for ewkt_to_shapely()."""

    def test_point_without_srid(self):
        geom = ewkt_to_shapely("POINT (30 10)")
        assert geom.geom_type == "Point"
        assert geom.x == 30.0
        assert geom.y == 10.0

    def test_point_with_srid_raises_on_shapely2(self):
        # Shapely 2.x does not allow setting arbitrary attributes on geometry objects.
        # ewkt_to_shapely tries to set geometry.srid, which fails.
        with pytest.raises(ValueError, match="Failed to parse EWKT"):
            ewkt_to_shapely("SRID=4326;POINT (30 10)")

    def test_empty_string_raises(self):
        with pytest.raises(ValueError):
            ewkt_to_shapely("")

    def test_none_raises(self):
        with pytest.raises(ValueError):
            ewkt_to_shapely(None)

    def test_invalid_wkt_raises(self):
        with pytest.raises(ValueError, match="Failed to parse EWKT"):
            ewkt_to_shapely("SRID=4326;GARBAGE()")

    def test_non_string_raises(self):
        with pytest.raises(ValueError):
            ewkt_to_shapely(123)


class TestShapelyToEwkt:
    """Tests for shapely_to_ewkt()."""

    def test_with_srid_param(self):
        result = shapely_to_ewkt(Point(30, 10), srid=4326)
        assert result.startswith("SRID=4326;")
        assert "POINT" in result

    def test_without_srid(self):
        result = shapely_to_ewkt(Point(30, 10))
        assert "SRID=" not in result
        assert "POINT" in result
