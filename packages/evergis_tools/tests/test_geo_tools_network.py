# -*- coding: utf-8 -*-
"""Tests for geo_tools/network.py -- routing and isochrone functions."""

import pytest
from shapely.geometry import Point

from evergis_tools.geo_tools.network import build_isochrone, build_route


def _feature_collection(geometry_dict):
    """Helper: wrap geometry dict into a GeoJSON FeatureCollection."""
    return {
        "type": "FeatureCollection",
        "features": [
            {
                "type": "Feature",
                "geometry": geometry_dict,
                "properties": {"gid": 1},
                "id": "1",
            }
        ],
        "totalCount": 1,
        "offset": 0,
        "limit": 0,
    }


class TestBuildIsochrone:
    """Tests for build_isochrone()."""

    def test_success_polygon_from_feature_collection(self, mock_client):
        mock_client.remotetaskmanager.post.return_value = _feature_collection(
            {"type": "Polygon", "coordinates": [[(0, 0), (1, 0), (1, 1), (0, 0)]], "srId": 4326}
        )
        result = build_isochrone(mock_client, Point(0, 0), duration=5)
        assert result is not None
        assert result.geom_type == "Polygon"

    def test_success_multipolygon_from_feature_collection(self, mock_client):
        mock_client.remotetaskmanager.post.return_value = _feature_collection(
            {"type": "MultiPolygon", "coordinates": [[[(0, 0), (1, 0), (1, 1), (0, 0)]]], "srId": 4326}
        )
        result = build_isochrone(mock_client, Point(0, 0), duration=5)
        assert result is not None
        assert result.geom_type == "MultiPolygon"

    def test_fallback_list_polygon(self, mock_client):
        """Legacy format: list of geometry dicts (fallback)."""
        mock_client.remotetaskmanager.post.return_value = [
            {"type": "polygon", "coordinates": [[(0, 0), (1, 0), (1, 1), (0, 0)]]}
        ]
        result = build_isochrone(mock_client, Point(0, 0), duration=5)
        assert result is not None
        assert result.geom_type == "Polygon"

    def test_unexpected_geometry_type(self, mock_client):
        mock_client.remotetaskmanager.post.return_value = _feature_collection(
            {"type": "Point", "coordinates": [0, 0], "srId": 4326}
        )
        result = build_isochrone(mock_client, Point(0, 0), duration=5, log=True)
        assert result is None

    def test_empty_features(self, mock_client):
        mock_client.remotetaskmanager.post.return_value = {
            "type": "FeatureCollection", "features": [], "totalCount": 0, "offset": 0, "limit": 0
        }
        result = build_isochrone(mock_client, Point(0, 0), duration=5)
        assert result is None

    def test_none_response(self, mock_client):
        mock_client.remotetaskmanager.post.return_value = None
        result = build_isochrone(mock_client, Point(0, 0), duration=5)
        assert result is None

    def test_exception_is_reraised(self, mock_client):
        # None is reserved for empty results; request errors propagate
        mock_client.remotetaskmanager.post.side_effect = RuntimeError("API error")
        with pytest.raises(RuntimeError, match="API error"):
            build_isochrone(mock_client, Point(0, 0), duration=5)


class TestBuildRoute:
    """Tests for build_route()."""

    def test_linestring_from_feature_collection(self, mock_client):
        mock_client.remotetaskmanager.post.return_value = _feature_collection(
            {"type": "MultiLineString", "coordinates": [[(0, 0), (1, 1)]], "srId": 4326}
        )
        result = build_route(mock_client, Point(0, 0), Point(1, 1))
        assert result is not None
        assert result.geom_type == "MultiLineString"

    def test_fallback_list_linestring(self, mock_client):
        """Legacy format: list of geometry dicts (fallback)."""
        mock_client.remotetaskmanager.post.return_value = [
            {"type": "linestring", "coordinates": [(0, 0), (1, 1)]}
        ]
        result = build_route(mock_client, Point(0, 0), Point(1, 1))
        assert result is not None
        assert result.geom_type == "LineString"

    def test_empty_response(self, mock_client):
        mock_client.remotetaskmanager.post.return_value = None
        result = build_route(mock_client, Point(0, 0), Point(1, 1))
        assert result is None

    def test_exception_is_reraised(self, mock_client):
        # None is reserved for empty results; request errors propagate
        mock_client.remotetaskmanager.post.side_effect = RuntimeError("API error")
        with pytest.raises(RuntimeError, match="API error"):
            build_route(mock_client, Point(0, 0), Point(1, 1))
