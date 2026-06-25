# -*- coding: utf-8 -*-
"""Tests for eql.py -- EQL query helpers (DataFrame / GeoDataFrame)."""

import pytest
import pandas as pd
import geopandas as gpd
from unittest.mock import MagicMock

from evergis_api.schemas import (
    EqlRequestDc,
    FeatureDc,
    GeometryAttributeConfigurationDc,
    PagedFeaturesListDc,
    PointDc,
    StringAttributeConfigurationDc,
)

from evergis_tools.eql import (
    _build_eql_request,
    _rows_from_result,
    _is_last_chunk,
    _combine_geodataframes,
    _describe_columns,
    _geometry_field_from_columns,
    eql_describe,
    eql_query_to_dataframe,
    eql_query_to_geodataframe,
)


# =====================================================================
# Helpers
# =====================================================================


def _make_feature(name: str, value: int, x: float = 30.0, y: float = 10.0):
    return FeatureDc(
        properties={"name": name, "value": value},
        geometry=PointDc(type="Point", coordinates=(x, y), srId=4326),
    )


def _make_page(features, limit=10, offset=0):
    return PagedFeaturesListDc(
        features=features,
        totalCount=len(features) if features else 0,
        limit=limit,
        offset=offset,
    )


def _mock_eql_client(pages):
    """Return a MagicMock client whose eql.get_paged_query_result returns
    pages in order.
    """
    client = MagicMock()
    client.eql.get_paged_query_result.side_effect = list(pages)
    return client


# =====================================================================
# _build_eql_request
# =====================================================================


class TestBuildEqlRequest:
    """Tests for _build_eql_request()."""

    def test_returns_eql_request_dc(self):
        req = _build_eql_request(
            query="SELECT * FROM em.layer",
            chunk_size=100,
            offset=0,
            columns=None,
            ds=None,
            geometry_field=None,
            id_field=None,
            parameters=None,
            with_geom=False,
        )
        assert isinstance(req, EqlRequestDc)
        assert req.query == "SELECT * FROM em.layer"
        assert req.limit == 100
        assert req.offset == 0
        assert req.withgeom is False

    def test_all_fields_passed_through(self):
        req = _build_eql_request(
            query="SELECT * FROM em.t",
            chunk_size=500,
            offset=1500,
            columns={"a": "string"},
            ds="dev",
            geometry_field="geom",
            id_field="oid",
            parameters={"@x": 1},
            with_geom=True,
        )
        assert req.limit == 500
        assert req.offset == 1500
        assert req.columns == {"a": "string"}
        assert req.ds == "dev"
        assert req.geometryField == "geom"
        assert req.idField == "oid"
        assert req.parameters == {"@x": 1}
        assert req.withgeom is True

    def test_with_geom_false_for_dataframe_query(self):
        req = _build_eql_request(
            query="SELECT count(*) FROM em.t",
            chunk_size=10,
            offset=0,
            columns=None,
            ds=None,
            geometry_field=None,
            id_field=None,
            parameters=None,
            with_geom=False,
        )
        assert req.withgeom is False
        assert req.geometryField is None


# =====================================================================
# _rows_from_result
# =====================================================================


class TestRowsFromResult:
    """Tests for _rows_from_result()."""

    def test_extracts_properties(self):
        page = _make_page([_make_feature("A", 1), _make_feature("B", 2)])
        rows = _rows_from_result(page)
        assert rows == [{"name": "A", "value": 1}, {"name": "B", "value": 2}]

    def test_empty_properties_dict_preserved(self):
        # Feature with empty properties dict must yield empty dict so
        # pandas can still stack the rows alongside populated ones.
        page = PagedFeaturesListDc(
            features=[FeatureDc(properties={}), FeatureDc(properties={"k": 1})],
            totalCount=2,
        )
        rows = _rows_from_result(page)
        assert rows == [{}, {"k": 1}]

    def test_empty_features(self):
        page = _make_page([])
        assert _rows_from_result(page) == []


# =====================================================================
# _is_last_chunk
# =====================================================================


class TestIsLastChunk:
    """Tests for _is_last_chunk()."""

    def test_empty_features_is_last(self):
        assert _is_last_chunk(_make_page([]), chunk_size=10) is True

    def test_partial_chunk_is_last(self):
        page = _make_page([_make_feature("A", 1)] * 5)
        assert _is_last_chunk(page, chunk_size=10) is True

    def test_full_chunk_is_not_last(self):
        page = _make_page([_make_feature("A", 1)] * 10)
        assert _is_last_chunk(page, chunk_size=10) is False

    def test_none_features_is_last(self):
        page = PagedFeaturesListDc(features=None, totalCount=0)
        assert _is_last_chunk(page, chunk_size=10) is True


# =====================================================================
# _combine_geodataframes
# =====================================================================


class TestCombineGeodataframes:
    """Tests for _combine_geodataframes()."""

    def test_empty_chunks_returns_empty_gdf(self):
        result = _combine_geodataframes([], target_crs="EPSG:4326")
        assert isinstance(result, gpd.GeoDataFrame)
        assert len(result) == 0
        assert "geometry" in result.columns

    def test_empty_chunks_respects_target_crs(self):
        result = _combine_geodataframes([], target_crs="EPSG:3857")
        assert str(result.crs) == "EPSG:3857"

    def test_single_chunk_passes_through(self, simple_point_gdf):
        result = _combine_geodataframes([simple_point_gdf], target_crs=None)
        assert len(result) == 3
        assert str(result.crs) == "EPSG:4326"

    def test_multiple_chunks_concatenated(self, simple_point_gdf):
        result = _combine_geodataframes(
            [simple_point_gdf, simple_point_gdf], target_crs=None
        )
        assert len(result) == 6
        assert str(result.crs) == "EPSG:4326"

    def test_resets_index(self, simple_point_gdf):
        # Concatenated frames must use a fresh 0..n-1 index, not the
        # duplicated source indices from each chunk.
        result = _combine_geodataframes(
            [simple_point_gdf, simple_point_gdf], target_crs=None
        )
        assert list(result.index) == [0, 1, 2, 3, 4, 5]


# =====================================================================
# eql_query_to_dataframe
# =====================================================================


class TestEqlQueryToDataframe:
    """Tests for eql_query_to_dataframe()."""

    def test_empty_result_returns_empty_dataframe(self):
        client = _mock_eql_client([_make_page([])])
        df = eql_query_to_dataframe("SELECT * FROM em.t", client)
        assert isinstance(df, pd.DataFrame)
        assert len(df) == 0

    def test_single_page_returns_correct_dataframe(self):
        client = _mock_eql_client([
            _make_page([_make_feature("A", 1), _make_feature("B", 2)]),
        ])
        df = eql_query_to_dataframe("SELECT * FROM em.t", client, chunk_size=10)

        assert isinstance(df, pd.DataFrame)
        assert len(df) == 2
        assert set(df.columns) == {"name", "value"}
        assert list(df["name"]) == ["A", "B"]
        assert list(df["value"]) == [1, 2]

    def test_partial_page_stops_pagination(self):
        # A page shorter than chunk_size is the final page -- no further
        # calls are needed.
        client = _mock_eql_client([
            _make_page([_make_feature("A", 1)]),
        ])
        df = eql_query_to_dataframe("SELECT * FROM em.t", client, chunk_size=10)

        assert len(df) == 1
        assert client.eql.get_paged_query_result.call_count == 1

    def test_multi_page_pagination(self):
        # Full chunk -> keep going; smaller chunk -> stop.
        page1 = _make_page([_make_feature(f"r{i}", i) for i in range(3)])
        page2 = _make_page([_make_feature(f"r{i}", i) for i in range(3, 5)])
        client = _mock_eql_client([page1, page2])

        df = eql_query_to_dataframe("SELECT * FROM em.t", client, chunk_size=3)

        assert len(df) == 5
        assert list(df["value"]) == [0, 1, 2, 3, 4]
        assert client.eql.get_paged_query_result.call_count == 2

    def test_multi_page_with_empty_terminator(self):
        # When every chunk is exactly chunk_size, pagination stops only on
        # an empty page.
        page1 = _make_page([_make_feature(f"r{i}", i) for i in range(2)])
        page2 = _make_page([_make_feature(f"r{i}", i) for i in range(2, 4)])
        page3 = _make_page([])
        client = _mock_eql_client([page1, page2, page3])

        df = eql_query_to_dataframe("SELECT * FROM em.t", client, chunk_size=2)

        assert len(df) == 4
        assert client.eql.get_paged_query_result.call_count == 3

    def test_offset_increments_between_pages(self):
        page1 = _make_page([_make_feature(f"r{i}", i) for i in range(2)])
        page2 = _make_page([_make_feature("last", 99)])
        client = _mock_eql_client([page1, page2])

        eql_query_to_dataframe("SELECT * FROM em.t", client, chunk_size=2)

        calls = client.eql.get_paged_query_result.call_args_list
        assert calls[0].kwargs["body"].offset == 0
        assert calls[1].kwargs["body"].offset == 2

    def test_parameters_passed_to_request(self):
        client = _mock_eql_client([_make_page([])])
        eql_query_to_dataframe(
            "SELECT * FROM em.t WHERE id = @id",
            client,
            parameters={"@id": 42},
        )

        body = client.eql.get_paged_query_result.call_args.kwargs["body"]
        assert body.parameters == {"@id": 42}

    def test_columns_and_ds_forwarded(self):
        client = _mock_eql_client([_make_page([])])
        eql_query_to_dataframe(
            "SELECT * FROM em.t",
            client,
            columns={"name": "string"},
            ds="dev",
            id_field="oid",
        )

        body = client.eql.get_paged_query_result.call_args.kwargs["body"]
        assert body.columns == {"name": "string"}
        assert body.ds == "dev"
        assert body.idField == "oid"

    def test_dataframe_request_has_no_geometry(self):
        client = _mock_eql_client([_make_page([])])
        eql_query_to_dataframe("SELECT * FROM em.t", client)

        body = client.eql.get_paged_query_result.call_args.kwargs["body"]
        assert body.withgeom is False

    def test_query_string_forwarded(self):
        client = _mock_eql_client([_make_page([])])
        query = "SELECT count(*) AS cnt FROM em.t GROUP BY type"
        eql_query_to_dataframe(query, client)

        body = client.eql.get_paged_query_result.call_args.kwargs["body"]
        assert body.query == query

    def test_backend_error_propagates(self):
        # A silent try/except here used to swallow real failures; ensure
        # the exception now surfaces to the caller.
        client = MagicMock()
        client.eql.get_paged_query_result.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            eql_query_to_dataframe("SELECT * FROM em.t", client)


# =====================================================================
# eql_query_to_geodataframe
# =====================================================================


class TestEqlQueryToGeodataframe:
    """Tests for eql_query_to_geodataframe()."""

    def test_empty_result_returns_empty_gdf(self):
        client = _mock_eql_client([_make_page([])])
        gdf = eql_query_to_geodataframe("SELECT * FROM em.t", client)

        assert isinstance(gdf, gpd.GeoDataFrame)
        assert len(gdf) == 0
        assert "geometry" in gdf.columns

    def test_empty_result_respects_target_crs(self):
        client = _mock_eql_client([_make_page([])])
        gdf = eql_query_to_geodataframe(
            "SELECT * FROM em.t", client, target_crs="EPSG:3857"
        )
        assert str(gdf.crs) == "EPSG:3857"

    def test_single_page_returns_correct_gdf(self):
        client = _mock_eql_client([
            _make_page([
                _make_feature("A", 1, x=30.0, y=10.0),
                _make_feature("B", 2, x=31.0, y=11.0),
            ]),
        ])
        gdf = eql_query_to_geodataframe("SELECT * FROM em.t", client, chunk_size=10)

        assert isinstance(gdf, gpd.GeoDataFrame)
        assert len(gdf) == 2
        assert "geometry" in gdf.columns
        assert list(gdf["name"]) == ["A", "B"]
        assert gdf.geometry.iloc[0].x == 30.0
        assert gdf.geometry.iloc[1].x == 31.0

    def test_multi_page_pagination(self):
        page1 = _make_page([
            _make_feature(f"r{i}", i, x=float(i), y=0.0) for i in range(3)
        ])
        page2 = _make_page([
            _make_feature(f"r{i}", i, x=float(i), y=0.0) for i in range(3, 5)
        ])
        client = _mock_eql_client([page1, page2])

        gdf = eql_query_to_geodataframe("SELECT * FROM em.t", client, chunk_size=3)

        assert len(gdf) == 5
        assert list(gdf["value"]) == [0, 1, 2, 3, 4]
        assert client.eql.get_paged_query_result.call_count == 2

    def test_partial_page_stops_pagination(self):
        client = _mock_eql_client([
            _make_page([_make_feature("only", 1)]),
        ])
        gdf = eql_query_to_geodataframe(
            "SELECT * FROM em.t", client, chunk_size=10
        )
        assert len(gdf) == 1
        assert client.eql.get_paged_query_result.call_count == 1

    def test_offset_increments_between_pages(self):
        page1 = _make_page([
            _make_feature(f"r{i}", i, x=float(i), y=0.0) for i in range(2)
        ])
        page2 = _make_page([_make_feature("last", 99, x=99.0, y=0.0)])
        client = _mock_eql_client([page1, page2])

        eql_query_to_geodataframe("SELECT * FROM em.t", client, chunk_size=2)

        calls = client.eql.get_paged_query_result.call_args_list
        assert calls[0].kwargs["body"].offset == 0
        assert calls[1].kwargs["body"].offset == 2

    def test_parameters_passed_to_request(self):
        client = _mock_eql_client([_make_page([])])
        eql_query_to_geodataframe(
            "SELECT * FROM em.t WHERE id = @id",
            client,
            parameters={"@id": 7},
        )

        body = client.eql.get_paged_query_result.call_args.kwargs["body"]
        assert body.parameters == {"@id": 7}

    def test_geometry_field_and_with_geom_defaults(self):
        client = _mock_eql_client([_make_page([])])
        eql_query_to_geodataframe("SELECT * FROM em.t", client)

        body = client.eql.get_paged_query_result.call_args.kwargs["body"]
        assert body.geometryField == "geometry"
        assert body.withgeom is True

    def test_custom_geometry_field(self):
        client = _mock_eql_client([_make_page([])])
        eql_query_to_geodataframe(
            "SELECT * FROM em.t",
            client,
            geometry_field="shape",
        )

        body = client.eql.get_paged_query_result.call_args.kwargs["body"]
        assert body.geometryField == "shape"

    def test_target_crs_applied_to_result(self):
        client = _mock_eql_client([
            _make_page([_make_feature("A", 1)]),
        ])
        gdf = eql_query_to_geodataframe(
            "SELECT * FROM em.t", client, target_crs="EPSG:4326"
        )
        assert gdf.crs is not None

    def test_query_string_forwarded(self):
        client = _mock_eql_client([_make_page([])])
        query = "SELECT * FROM em.t WHERE type = 'shop'"
        eql_query_to_geodataframe(query, client)

        body = client.eql.get_paged_query_result.call_args.kwargs["body"]
        assert body.query == query

    def test_backend_error_propagates(self):
        client = MagicMock()
        client.eql.get_paged_query_result.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            eql_query_to_geodataframe("SELECT * FROM em.t", client)

    def test_with_geom_false_forwarded(self):
        client = _mock_eql_client([_make_page([])])
        eql_query_to_geodataframe(
            "SELECT * FROM em.t", client, with_geom=False
        )

        body = client.eql.get_paged_query_result.call_args.kwargs["body"]
        assert body.withgeom is False


# =====================================================================
# eql_describe / column helpers
# =====================================================================


def _make_columns(geom_name="geometry"):
    """Build a typical get_query_description result: string + geometry."""
    return [
        StringAttributeConfigurationDc(attributeName="name", type="String"),
        GeometryAttributeConfigurationDc(attributeName=geom_name, type="Point"),
    ]


class TestDescribeColumns:
    """Tests for _describe_columns() and _geometry_field_from_columns()."""

    def test_maps_kind_and_geometry_flag(self):
        cols = _describe_columns(_make_columns())
        by_name = {c["name"]: c for c in cols}

        assert by_name["name"]["kind"] == "string"
        assert by_name["name"]["is_geometry"] is False
        assert by_name["geometry"]["kind"] == "geometry"
        assert by_name["geometry"]["is_geometry"] is True
        assert by_name["geometry"]["type"] == "Point"

    def test_geometry_field_detects_name(self):
        assert _geometry_field_from_columns(_describe_columns(_make_columns("geom"))) == "geom"

    def test_geometry_field_none_when_absent(self):
        cols = _describe_columns(
            [StringAttributeConfigurationDc(attributeName="name", type="String")]
        )
        assert _geometry_field_from_columns(cols) is None


class TestEqlDescribe:
    """Tests for eql_describe()."""

    def test_calls_get_query_description_with_query(self):
        client = MagicMock()
        client.eql.get_query_description.return_value = _make_columns()

        cols = eql_describe("SELECT * FROM em.t", client)

        body = client.eql.get_query_description.call_args.kwargs["body"]
        assert body.query == "SELECT * FROM em.t"
        assert {c["name"] for c in cols} == {"name", "geometry"}

    def test_forwards_ds_and_parameters(self):
        client = MagicMock()
        client.eql.get_query_description.return_value = _make_columns()

        eql_describe(
            "SELECT * FROM em.t WHERE id = @id",
            client,
            ds="some_ds",
            parameters={"@id": 1},
        )

        body = client.eql.get_query_description.call_args.kwargs["body"]
        assert body.ds == "some_ds"
        assert body.parameters == {"@id": 1}


class TestGeometryFieldAuto:
    """Tests for geometry_field='auto' in eql_query_to_geodataframe()."""

    def test_auto_detects_geom_column(self):
        client = _mock_eql_client([_make_page([])])
        client.eql.get_query_description.return_value = _make_columns("geom")

        eql_query_to_geodataframe("SELECT * FROM em.t", client, geometry_field="auto")

        body = client.eql.get_paged_query_result.call_args.kwargs["body"]
        assert body.geometryField == "geom"

    def test_auto_falls_back_to_geometry_when_describe_fails(self):
        client = _mock_eql_client([_make_page([])])
        client.eql.get_query_description.side_effect = RuntimeError("boom")

        eql_query_to_geodataframe("SELECT * FROM em.t", client, geometry_field="auto")

        body = client.eql.get_paged_query_result.call_args.kwargs["body"]
        assert body.geometryField == "geometry"
