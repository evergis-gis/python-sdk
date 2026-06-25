# -*- coding: utf-8 -*-
"""Tests for geometry/validators.py -- pure validation functions."""

import pytest
from shapely.geometry import Point

from evergis_tools.geometry.validators import (
    assert_geometry_instance,
    validate_srid,
    validate_geometry_type,
    validate_ewkt_format,
    validate_coordinates,
    validate_bbox,
    validate_geojson_feature,
)


class TestAssertGeometryInstance:
    """Tests for assert_geometry_instance()."""

    def test_correct_type_passes(self):
        assert_geometry_instance(Point(0, 0), Point, "Point")

    def test_wrong_type_raises(self):
        with pytest.raises(ValueError, match="Expected Point"):
            assert_geometry_instance("not a point", Point, "Point")

    def test_error_includes_actual_type(self):
        with pytest.raises(ValueError, match="got str"):
            assert_geometry_instance("string", Point, "Point")


class TestValidateSrid:
    """Tests for validate_srid()."""

    @pytest.mark.parametrize("srid", [4326, 3857, 1, 32767])
    def test_valid(self, srid):
        assert validate_srid(srid) is True

    def test_string_srid(self):
        assert validate_srid("4326") is True

    @pytest.mark.parametrize("srid", [0, -1, 32768])
    def test_out_of_range(self, srid):
        assert validate_srid(srid) is False

    def test_non_numeric_string(self):
        assert validate_srid("abc") is False

    def test_none(self):
        assert validate_srid(None) is False


class TestValidateGeometryType:
    """Tests for validate_geometry_type()."""

    @pytest.mark.parametrize("geom_type", [
        "Point", "LineString", "Polygon", "MultiPoint",
        "MultiLineString", "MultiPolygon", "GeometryCollection",
    ])
    def test_valid_types(self, geom_type):
        assert validate_geometry_type(geom_type) is True

    def test_invalid_type(self):
        assert validate_geometry_type("InvalidType") is False

    def test_case_sensitive(self):
        assert validate_geometry_type("point") is False

    def test_empty_string(self):
        assert validate_geometry_type("") is False

    def test_non_string(self):
        assert validate_geometry_type(123) is False

    def test_none(self):
        assert validate_geometry_type(None) is False


class TestValidateEwktFormat:
    """Tests for validate_ewkt_format()."""

    @pytest.mark.parametrize("ewkt", [
        "SRID=4326;POINT(30 10)",
        "POINT(30 10)",
        "SRID=3857;POLYGON((0 0, 1 0, 1 1, 0 0))",
        "LINESTRING(0 0, 1 1)",
        "MULTIPOLYGON(((0 0, 1 0, 1 1, 0 0)))",
        "GEOMETRYCOLLECTION(POINT(0 0))",
    ])
    def test_valid(self, ewkt):
        assert validate_ewkt_format(ewkt) is True

    def test_case_insensitive(self):
        assert validate_ewkt_format("srid=4326;point(30 10)") is True

    @pytest.mark.parametrize("ewkt", ["INVALID", "", "   "])
    def test_invalid(self, ewkt):
        assert validate_ewkt_format(ewkt) is False

    def test_non_string(self):
        assert validate_ewkt_format(123) is False

    def test_none(self):
        assert validate_ewkt_format(None) is False


class TestValidateCoordinates:
    """Tests for validate_coordinates()."""

    def test_valid_2d(self):
        assert validate_coordinates([30.0, 10.0]) is True

    def test_valid_3d(self):
        assert validate_coordinates([30.0, 10.0, 5.0], dimension=3) is True

    def test_too_few(self):
        assert validate_coordinates([30.0]) is False

    def test_too_few_for_3d(self):
        assert validate_coordinates([30.0, 10.0], dimension=3) is False

    def test_non_numeric(self):
        assert validate_coordinates(["a", "b"]) is False

    def test_not_a_list(self):
        assert validate_coordinates((30.0, 10.0)) is False

    def test_extra_coords_valid(self):
        assert validate_coordinates([30.0, 10.0, 5.0], dimension=2) is True


class TestValidateBbox:
    """Tests for validate_bbox()."""

    def test_valid(self):
        assert validate_bbox([10.0, 20.0, 30.0, 40.0]) is True

    def test_minx_greater_than_maxx(self):
        assert validate_bbox([30.0, 20.0, 10.0, 40.0]) is False

    def test_miny_greater_than_maxy(self):
        assert validate_bbox([10.0, 40.0, 30.0, 20.0]) is False

    def test_equal_min_max(self):
        assert validate_bbox([10.0, 20.0, 10.0, 40.0]) is False

    def test_wrong_length(self):
        assert validate_bbox([10.0, 20.0, 30.0]) is False

    def test_non_numeric(self):
        assert validate_bbox([10.0, "a", 30.0, 40.0]) is False

    def test_not_a_list(self):
        assert validate_bbox((10.0, 20.0, 30.0, 40.0)) is False


class TestValidateGeojsonFeature:
    """Tests for validate_geojson_feature()."""

    def test_valid(self):
        feature = {
            "type": "Feature",
            "geometry": {"type": "Point", "coordinates": [30, 10]},
            "properties": {"name": "Test"},
        }
        assert validate_geojson_feature(feature) is True

    def test_null_geometry(self):
        feature = {"type": "Feature", "geometry": None, "properties": {"name": "Test"}}
        assert validate_geojson_feature(feature) is True

    def test_wrong_type(self):
        feature = {"type": "FeatureCollection", "geometry": None, "properties": {}}
        assert validate_geojson_feature(feature) is False

    def test_missing_geometry_key(self):
        assert validate_geojson_feature({"type": "Feature", "properties": {}}) is False

    def test_missing_properties_key(self):
        assert validate_geojson_feature({"type": "Feature", "geometry": None}) is False

    def test_properties_not_dict(self):
        feature = {"type": "Feature", "geometry": None, "properties": "bad"}
        assert validate_geojson_feature(feature) is False

    def test_geometry_not_dict(self):
        feature = {"type": "Feature", "geometry": "bad", "properties": {}}
        assert validate_geojson_feature(feature) is False

    def test_geometry_invalid_type(self):
        feature = {
            "type": "Feature",
            "geometry": {"type": "BadType", "coordinates": [0, 0]},
            "properties": {},
        }
        assert validate_geojson_feature(feature) is False

    def test_not_a_dict(self):
        assert validate_geojson_feature("string") is False

    def test_none(self):
        assert validate_geojson_feature(None) is False
