# -*- coding: utf-8 -*-
"""Tests for geometry/shapely.py -- GeoJSON-native conversion."""

import pytest

from evergis_api.schemas import (
    PointDc,
    LineStringDc,
    PolygonDc,
    MultiPolygonDc,
    MultiPointDc,
    MultiLineStringDc,
    EnvelopeDc,
)
from evergis_tools.geometry.shapely import (
    shapely_to_evergis_geometry,
    evergis_geometry_to_shapely,
    evergis_dict_to_shapely,
)


class TestShapelyToEvergisGeometry:
    """Tests for shapely_to_evergis_geometry()."""

    def test_point(self, shapely_point):
        result = shapely_to_evergis_geometry(shapely_point, sr_id=4326)
        assert isinstance(result, PointDc)
        assert result.coordinates == (30.0, 10.0)
        assert result.srId == 4326
        assert result.type == "Point"

    def test_linestring(self, shapely_linestring):
        result = shapely_to_evergis_geometry(shapely_linestring, sr_id=3857)
        assert isinstance(result, LineStringDc)
        assert len(result.coordinates) == 3
        assert result.srId == 3857
        assert result.type == "LineString"

    def test_polygon(self, shapely_polygon):
        result = shapely_to_evergis_geometry(shapely_polygon, sr_id=4326)
        assert isinstance(result, PolygonDc)
        assert len(result.coordinates) >= 1
        assert len(result.coordinates[0]) == 5
        assert result.type == "Polygon"

    def test_multipoint(self, shapely_multipoint):
        result = shapely_to_evergis_geometry(shapely_multipoint, sr_id=4326)
        assert isinstance(result, MultiPointDc)
        assert len(result.coordinates) == 2

    def test_multilinestring(self, shapely_multilinestring):
        result = shapely_to_evergis_geometry(shapely_multilinestring, sr_id=4326)
        assert isinstance(result, MultiLineStringDc)
        assert len(result.coordinates) == 2

    def test_multipolygon(self, shapely_multipolygon):
        result = shapely_to_evergis_geometry(shapely_multipolygon, sr_id=4326)
        assert isinstance(result, MultiPolygonDc)
        assert len(result.coordinates) == 2

    @pytest.mark.parametrize("sr_id", [4326, 3857, 32637, 1])
    def test_srid_propagated(self, shapely_point, sr_id):
        result = shapely_to_evergis_geometry(shapely_point, sr_id=sr_id)
        assert result.srId == sr_id

    def test_geometry_collection_raises(self, shapely_geometry_collection):
        with pytest.raises(ValueError, match="Unsupported geometry type"):
            shapely_to_evergis_geometry(shapely_geometry_collection, sr_id=4326)

    def test_roundtrip_point(self, shapely_point):
        dc = shapely_to_evergis_geometry(shapely_point, sr_id=4326)
        back = evergis_geometry_to_shapely(dc)
        assert back.equals(shapely_point)

    def test_roundtrip_linestring(self, shapely_linestring):
        dc = shapely_to_evergis_geometry(shapely_linestring, sr_id=4326)
        back = evergis_geometry_to_shapely(dc)
        assert back.equals(shapely_linestring)

    def test_roundtrip_polygon(self, shapely_polygon):
        dc = shapely_to_evergis_geometry(shapely_polygon, sr_id=4326)
        back = evergis_geometry_to_shapely(dc)
        assert back.equals(shapely_polygon)

    def test_roundtrip_multipolygon(self, shapely_multipolygon):
        dc = shapely_to_evergis_geometry(shapely_multipolygon, sr_id=4326)
        back = evergis_geometry_to_shapely(dc)
        assert back.equals(shapely_multipolygon)

    def test_roundtrip_multilinestring(self, shapely_multilinestring):
        dc = shapely_to_evergis_geometry(shapely_multilinestring, sr_id=4326)
        back = evergis_geometry_to_shapely(dc)
        assert back.equals(shapely_multilinestring)

    def test_roundtrip_multipoint(self, shapely_multipoint):
        dc = shapely_to_evergis_geometry(shapely_multipoint, sr_id=4326)
        back = evergis_geometry_to_shapely(dc)
        assert back.equals(shapely_multipoint)


class TestEvergisGeometryToShapely:
    """Tests for evergis_geometry_to_shapely()."""

    def test_point_dc(self, point_dc):
        result = evergis_geometry_to_shapely(point_dc)
        assert result.geom_type == "Point"
        assert result.x == 30.0
        assert result.y == 10.0

    def test_linestring_dc(self, linestring_dc):
        result = evergis_geometry_to_shapely(linestring_dc)
        assert result.geom_type == "LineString"
        assert len(result.coords) == 3

    def test_polygon_dc(self, polygon_dc):
        result = evergis_geometry_to_shapely(polygon_dc)
        assert result.geom_type == "Polygon"
        assert result.is_valid

    def test_envelope_dc(self, envelope_dc):
        result = evergis_geometry_to_shapely(envelope_dc)
        assert result.geom_type == "Polygon"
        assert result.bounds == (0.0, 0.0, 1.0, 1.0)

    def test_envelope_dc_three_coordinates_raises(self):
        bad = EnvelopeDc(coordinates=[(0.0, 0.0), (1.0, 1.0), (2.0, 2.0)])
        with pytest.raises(ValueError, match="exactly 2 coordinates"):
            evergis_geometry_to_shapely(bad)

    def test_envelope_dc_one_coordinate_raises(self):
        bad = EnvelopeDc(coordinates=[(0.0, 0.0)])
        with pytest.raises(ValueError, match="exactly 2 coordinates"):
            evergis_geometry_to_shapely(bad)


class TestEvergisDictToShapely:
    """Tests for evergis_dict_to_shapely()."""

    def test_geojson_point(self):
        result = evergis_dict_to_shapely({"type": "Point", "coordinates": [30.0, 10.0]})
        assert result.geom_type == "Point"
        assert result.x == 30.0

    def test_geojson_polygon(self):
        result = evergis_dict_to_shapely({
            "type": "Polygon",
            "coordinates": [[(0, 0), (1, 0), (1, 1), (0, 1), (0, 0)]],
        })
        assert result.geom_type == "Polygon"

    @pytest.mark.parametrize("old_type,expected_geom_type", [
        ("polyline", "MultiLineString"),
        ("polygon", "Polygon"),
        ("point", "Point"),
        ("multipolygon", "MultiPolygon"),
        ("multipoint", "MultiPoint"),
        ("linestring", "LineString"),
        ("multilinestring", "MultiLineString"),
        ("line", "LineString"),
    ])
    def test_old_format_type_mapping(self, old_type, expected_geom_type):
        coord_map = {
            "Point": [0.0, 0.0],
            "LineString": [[0.0, 0.0], [1.0, 1.0]],
            "MultiLineString": [[[0.0, 0.0], [1.0, 1.0]]],
            "Polygon": [[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]],
            "MultiPolygon": [[[[0.0, 0.0], [1.0, 0.0], [1.0, 1.0], [0.0, 0.0]]]],
            "MultiPoint": [[0.0, 0.0], [1.0, 1.0]],
        }
        result = evergis_dict_to_shapely({
            "type": old_type,
            "coordinates": coord_map[expected_geom_type],
        })
        assert result.geom_type == expected_geom_type

    def test_not_a_dict_raises(self):
        with pytest.raises(ValueError, match="must be a dict"):
            evergis_dict_to_shapely("not a dict")

    def test_missing_type_raises(self):
        with pytest.raises(ValueError, match="must contain 'type'"):
            evergis_dict_to_shapely({"coordinates": [0, 0]})

    def test_missing_coordinates_raises(self):
        with pytest.raises(ValueError, match="must contain 'coordinates'"):
            evergis_dict_to_shapely({"type": "Point"})

    def test_none_raises(self):
        with pytest.raises(ValueError, match="must be a dict"):
            evergis_dict_to_shapely(None)
