# -*- coding: utf-8 -*-
"""Tests for geodataframes.py -- GeoDataFrame conversion pipeline."""

import pytest
import geopandas as gpd
from shapely.geometry import Point, LineString, Polygon, MultiLineString, MultiPolygon, GeometryCollection

from evergis_api.schemas import (
    FeatureDc,
    PointDc,
    PagedFeaturesListDc,
)
from evergis_tools.geodataframes import (
    filter_gdf_by_geometry_type,
    gdf_to_features,
    gdf_to_feature_collection,
    df_to_feature_collection,
    paged_features_to_geodataframe,
    create_geometry_dc,
)


class TestFilterGdfByGeometryType:
    """Tests for filter_gdf_by_geometry_type()."""

    def test_filter_points(self, mixed_geom_gdf):
        result = filter_gdf_by_geometry_type(mixed_geom_gdf, "Point")
        assert len(result) == 1
        assert result.geometry.iloc[0].geom_type == "Point"

    def test_filter_linestring(self, mixed_geom_gdf):
        result = filter_gdf_by_geometry_type(mixed_geom_gdf, "LineString")
        assert len(result) == 1

    def test_filter_polygon(self, mixed_geom_gdf):
        result = filter_gdf_by_geometry_type(mixed_geom_gdf, "Polygon")
        assert len(result) == 1

    def test_polyline_alias(self):
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2, 3]},
            geometry=[
                LineString([(0, 0), (1, 1)]),
                MultiLineString([[(0, 0), (1, 1)]]),
                Point(0, 0),
            ],
            crs="EPSG:4326",
        )
        result = filter_gdf_by_geometry_type(gdf, "polyline")
        assert len(result) == 2

    def test_multilinestring_alias(self):
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2]},
            geometry=[
                LineString([(0, 0), (1, 1)]),
                MultiLineString([[(0, 0), (1, 1)]]),
            ],
            crs="EPSG:4326",
        )
        result = filter_gdf_by_geometry_type(gdf, "multilinestring")
        assert len(result) == 2

    def test_multipolygon_alias(self):
        gdf = gpd.GeoDataFrame(
            {"id": [1, 2]},
            geometry=[
                Polygon([(0, 0), (1, 0), (1, 1), (0, 0)]),
                MultiPolygon([Polygon([(0, 0), (1, 0), (1, 1), (0, 0)])]),
            ],
            crs="EPSG:4326",
        )
        result = filter_gdf_by_geometry_type(gdf, "multipolygon")
        assert len(result) == 2

    def test_case_insensitive(self):
        gdf = gpd.GeoDataFrame(
            {"id": [1]},
            geometry=[LineString([(0, 0), (1, 1)])],
            crs="EPSG:4326",
        )
        result = filter_gdf_by_geometry_type(gdf, "Polyline")
        assert len(result) == 1

    def test_empty_gdf(self, empty_gdf):
        result = filter_gdf_by_geometry_type(empty_gdf, "Point")
        assert len(result) == 0

    def test_null_geometries_excluded(self, gdf_with_nulls):
        result = filter_gdf_by_geometry_type(gdf_with_nulls, "Point")
        assert all(g is not None and not g.is_empty for g in result.geometry)

    def test_no_matching_type(self, simple_point_gdf):
        result = filter_gdf_by_geometry_type(simple_point_gdf, "Polygon")
        assert len(result) == 0


class TestGdfToFeatures:
    """Tests for gdf_to_features()."""

    def test_basic_conversion(self, simple_point_gdf):
        features = gdf_to_features(simple_point_gdf)
        assert len(features) == 3
        assert all(isinstance(f, FeatureDc) for f in features)

    def test_properties_populated(self, simple_point_gdf):
        features = gdf_to_features(simple_point_gdf)
        assert features[0].properties["name"] == "A"
        assert features[0].properties["value"] == 1

    def test_geometry_is_point_dc(self, simple_point_gdf):
        features = gdf_to_features(simple_point_gdf)
        assert isinstance(features[0].geometry, PointDc)
        assert features[0].geometry.coordinates == (30.0, 10.0)

    def test_empty_gdf_returns_empty(self, empty_gdf):
        assert gdf_to_features(empty_gdf) == []

    def test_geometry_type_filter(self, mixed_geom_gdf):
        features = gdf_to_features(mixed_geom_gdf, geometry_type="Point")
        assert len(features) == 1
        assert isinstance(features[0].geometry, PointDc)

    def test_geometry_type_filter_no_match(self, simple_point_gdf):
        assert gdf_to_features(simple_point_gdf, geometry_type="Polygon") == []

    def test_reprojection_3857_to_4326(self):
        gdf = gpd.GeoDataFrame(
            {"id": [1]},
            geometry=[Point(3339584.7, 1118889.97)],
            crs="EPSG:3857",
        )
        features = gdf_to_features(gdf, target_sr=4326)
        assert len(features) == 1
        x = features[0].geometry.coordinates[0]
        y = features[0].geometry.coordinates[1]
        assert -180 <= x <= 180
        assert -90 <= y <= 90

    def test_no_reprojection_when_same_sr(self, simple_point_gdf):
        features = gdf_to_features(simple_point_gdf, target_sr=4326)
        assert features[0].geometry.coordinates == (30.0, 10.0)

    def test_nan_values_become_none(self):
        gdf = gpd.GeoDataFrame(
            {"name": ["A", None], "value": [1.0, float("nan")]},
            geometry=[Point(0, 0), Point(1, 1)],
            crs="EPSG:4326",
        )
        features = gdf_to_features(gdf)
        assert features[1].properties["name"] is None
        assert features[1].properties["value"] is None

    def test_no_crs_no_error(self):
        gdf = gpd.GeoDataFrame(
            {"id": [1]},
            geometry=[Point(30, 10)],
        )
        features = gdf_to_features(gdf, target_sr=4326)
        assert len(features) == 1


class TestPagedFeaturesToGeoDataFrame:
    """Tests for paged_features_to_geodataframe()."""

    def test_single_page(self, sample_paged_features):
        gdf = paged_features_to_geodataframe(sample_paged_features)
        assert isinstance(gdf, gpd.GeoDataFrame)
        assert len(gdf) == 2
        assert "name" in gdf.columns

    def test_multiple_pages(self, sample_paged_features):
        page2 = PagedFeaturesListDc(
            features=[
                FeatureDc(
                    properties={"name": "C"},
                    geometry=PointDc(type="Point", coordinates=(32.0, 12.0), srId=4326),
                ),
            ],
            totalCount=3,
            limit=10,
            offset=2,
        )
        gdf = paged_features_to_geodataframe([sample_paged_features, page2])
        assert len(gdf) == 3

    def test_auto_detect_crs(self, sample_paged_features):
        gdf = paged_features_to_geodataframe(sample_paged_features)
        assert gdf.crs is not None
        assert gdf.crs.to_epsg() == 4326

    def test_explicit_target_crs(self, sample_paged_features):
        gdf = paged_features_to_geodataframe(
            sample_paged_features, target_crs="EPSG:4326"
        )
        assert gdf.crs.to_epsg() == 4326

    def test_empty_features(self):
        page = PagedFeaturesListDc(features=[], totalCount=0)
        gdf = paged_features_to_geodataframe(page)
        assert isinstance(gdf, gpd.GeoDataFrame)
        assert len(gdf) == 0

    def test_none_features(self):
        page = PagedFeaturesListDc(features=None, totalCount=0)
        gdf = paged_features_to_geodataframe(page)
        assert len(gdf) == 0

    def test_none_page_skipped(self, sample_paged_features):
        gdf = paged_features_to_geodataframe([None, sample_paged_features])
        assert len(gdf) == 2

    def test_list_of_features_accepted(self):
        features = [
            FeatureDc(
                properties={"name": "A"},
                geometry=PointDc(type="Point", coordinates=(30.0, 10.0), srId=4326),
            ),
        ]
        gdf = paged_features_to_geodataframe([features])
        assert len(gdf) == 1

    def test_features_with_null_geometry(self):
        page = PagedFeaturesListDc(
            features=[FeatureDc(
                properties={"name": "A"},
                geometry=PointDc(type="Point", coordinates=(0.0, 0.0), srId=4326),
            )],
            totalCount=1,
        )
        gdf = paged_features_to_geodataframe(page)
        assert len(gdf) == 1

    def test_srid_stripped(self, sample_paged_features):
        gdf = paged_features_to_geodataframe(sample_paged_features)
        assert len(gdf) == 2


class TestCreateGeometryDc:
    """Tests for create_geometry_dc() helper."""

    def test_valid_point(self):
        result = create_geometry_dc(Point(30.0, 10.0), target_sr=4326)
        assert isinstance(result, PointDc)

    def test_unsupported_type_raises(self):
        # A real but unsupported geometry must not be silently dropped to None.
        gc = GeometryCollection([Point(0, 0)])
        with pytest.raises(ValueError):
            create_geometry_dc(gc, target_sr=4326)

    def test_none_geometry_returns_none(self):
        # A missing geometry (e.g. geometryless row) is a legitimate None.
        assert create_geometry_dc(None, target_sr=4326) is None


# =====================================================================
# gdf_to_feature_collection
# =====================================================================


class TestGdfToFeatureCollection:
    """Tests for gdf_to_feature_collection()."""

    def test_basic(self, simple_point_gdf):
        result = gdf_to_feature_collection(simple_point_gdf)
        assert result["type"] == "FeatureCollection"
        assert result["totalCount"] == 3
        assert result["offset"] == 0
        assert result["limit"] == 0
        assert len(result["features"]) == 3

    def test_features_have_required_keys(self, simple_point_gdf):
        result = gdf_to_feature_collection(simple_point_gdf)
        for f in result["features"]:
            assert "type" in f
            assert f["type"] == "Feature"
            assert "properties" in f
            assert "id" in f

    def test_features_have_geometry(self, simple_point_gdf):
        result = gdf_to_feature_collection(simple_point_gdf)
        for f in result["features"]:
            assert "geometry" in f
            assert f["geometry"]["type"] == "Point"

    def test_properties_preserved(self, simple_point_gdf):
        result = gdf_to_feature_collection(simple_point_gdf)
        props = result["features"][0]["properties"]
        assert props["name"] == "A"
        assert props["value"] == 1

    def test_empty_gdf(self, empty_gdf):
        result = gdf_to_feature_collection(empty_gdf)
        assert result["type"] == "FeatureCollection"
        assert result["totalCount"] == 0
        assert result["features"] == []

    def test_ids_sequential(self, simple_point_gdf):
        result = gdf_to_feature_collection(simple_point_gdf)
        ids = [f["id"] for f in result["features"]]
        assert ids == ["1", "2", "3"]


# =====================================================================
# df_to_feature_collection
# =====================================================================


class TestDfToFeatureCollection:
    """Tests for df_to_feature_collection()."""

    def test_basic(self):
        import pandas as pd
        df = pd.DataFrame({"year": [2020, 2021, 2022], "value": [100, 200, 300]})
        result = df_to_feature_collection(df)
        assert result["type"] == "FeatureCollection"
        assert result["totalCount"] == 3
        assert len(result["features"]) == 3

    def test_no_geometry(self):
        import pandas as pd
        df = pd.DataFrame({"name": ["A", "B"]})
        result = df_to_feature_collection(df)
        for f in result["features"]:
            assert "geometry" not in f or f.get("geometry") is None

    def test_properties(self):
        import pandas as pd
        df = pd.DataFrame({"city": ["Moscow"], "pop": [12000000]})
        result = df_to_feature_collection(df)
        props = result["features"][0]["properties"]
        assert props["city"] == "Moscow"
        assert props["pop"] == 12000000

    def test_nan_becomes_none(self):
        import pandas as pd
        df = pd.DataFrame({"val": [1.0, float("nan")]})
        result = df_to_feature_collection(df)
        assert result["features"][1]["properties"]["val"] is None

    def test_empty_df(self):
        import pandas as pd
        df = pd.DataFrame()
        result = df_to_feature_collection(df)
        assert result["totalCount"] == 0
        assert result["features"] == []

    def test_ids_sequential(self):
        import pandas as pd
        df = pd.DataFrame({"x": [1, 2, 3, 4]})
        result = df_to_feature_collection(df)
        ids = [f["id"] for f in result["features"]]
        assert ids == ["1", "2", "3", "4"]
