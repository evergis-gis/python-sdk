# -*- coding: utf-8 -*-
"""Tests for evergis_tools._async EQL helpers -- unit tests, no network."""

import asyncio
import inspect

import pytest
from unittest.mock import AsyncMock, MagicMock

from evergis_api.schemas import (
    FeatureDc,
    PagedFeaturesListDc,
    PointDc,
)

from evergis_tools._async import (
    eql_describe,
    eql_query_to_dataframe,
    eql_query_to_geodataframe,
)
from evergis_tools import _async as async_module


# ---------------------------------------------------------------------------
# Helpers
# ---------------------------------------------------------------------------


def _make_paged(features, total=None, limit=10, offset=0):
    """Build PagedFeaturesListDc for mock responses."""
    return PagedFeaturesListDc(
        features=features,
        totalCount=total if total is not None else len(features),
        limit=limit,
        offset=offset,
    )


def _empty_paged():
    return _make_paged([], total=0)


def _make_feature(props, with_geom=True, x=30.0, y=10.0):
    geom = PointDc(type="Point", coordinates=(x, y), srId=4326) if with_geom else None
    return FeatureDc(properties=props, geometry=geom)


def _build_async_client(*page_results):
    """Create a mock AsyncClient whose eql.get_paged_query_result returns the
    given pages in order on successive awaits."""
    client = MagicMock()
    client.eql = MagicMock()
    client.eql.get_paged_query_result = AsyncMock(side_effect=list(page_results))
    return client


# ---------------------------------------------------------------------------
# Module-level checks
# ---------------------------------------------------------------------------


class TestModuleExports:
    """Tests for the public surface of evergis_tools._async."""

    def test_dataframe_export_present(self):
        assert hasattr(async_module, "eql_query_to_dataframe")
        assert async_module.eql_query_to_dataframe is eql_query_to_dataframe

    def test_geodataframe_export_present(self):
        assert hasattr(async_module, "eql_query_to_geodataframe")
        assert async_module.eql_query_to_geodataframe is eql_query_to_geodataframe

    def test_describe_export_present(self):
        assert hasattr(async_module, "eql_describe")
        assert async_module.eql_describe is eql_describe

    def test_all_lists_both(self):
        assert set(async_module.__all__) == {
            "eql_describe",
            "eql_query_to_dataframe",
            "eql_query_to_geodataframe",
        }


class TestSignatures:
    """Tests that exported callables are coroutine functions with expected args."""

    def test_dataframe_is_coroutine_function(self):
        assert inspect.iscoroutinefunction(eql_query_to_dataframe)

    def test_geodataframe_is_coroutine_function(self):
        assert inspect.iscoroutinefunction(eql_query_to_geodataframe)

    def test_dataframe_signature(self):
        sig = inspect.signature(eql_query_to_dataframe)
        # query + client must be there; the rest defaults so callers stay terse.
        assert "query" in sig.parameters
        assert "client" in sig.parameters
        assert "chunk_size" in sig.parameters
        assert "parameters" in sig.parameters

    def test_geodataframe_signature(self):
        sig = inspect.signature(eql_query_to_geodataframe)
        assert "query" in sig.parameters
        assert "client" in sig.parameters
        assert "geometry_field" in sig.parameters
        assert "with_geom" in sig.parameters
        assert "target_crs" in sig.parameters


# ---------------------------------------------------------------------------
# eql_query_to_dataframe
# ---------------------------------------------------------------------------


class TestEqlQueryToDataframe:
    """Tests for the async DataFrame helper."""

    def test_single_page_returns_dataframe(self):
        features = [
            _make_feature({"name": "A", "value": 1}, with_geom=False),
            _make_feature({"name": "B", "value": 2}, with_geom=False),
        ]
        # Single page that's smaller than chunk_size -> loop exits immediately.
        client = _build_async_client(_make_paged(features, limit=1000))

        df = asyncio.run(
            eql_query_to_dataframe("SELECT name, value FROM t", client, chunk_size=1000)
        )

        assert len(df) == 2
        assert set(df.columns) == {"name", "value"}
        assert list(df["name"]) == ["A", "B"]
        assert list(df["value"]) == [1, 2]
        # One server call -- short-circuited on a partial page.
        client.eql.get_paged_query_result.assert_awaited_once()

    def test_empty_result_returns_empty_dataframe(self):
        client = _build_async_client(_empty_paged())

        df = asyncio.run(
            eql_query_to_dataframe("SELECT * FROM t", client, chunk_size=1000)
        )

        assert len(df) == 0
        # Empty features -> we never enter the row-extraction branch.
        assert list(df.columns) == []
        client.eql.get_paged_query_result.assert_awaited_once()

    def test_multipage_pagination(self):
        # Two full chunks of size 2 followed by an empty page = pagination.
        chunk = [
            _make_feature({"v": 1}, with_geom=False),
            _make_feature({"v": 2}, with_geom=False),
        ]
        chunk2 = [
            _make_feature({"v": 3}, with_geom=False),
            _make_feature({"v": 4}, with_geom=False),
        ]
        client = _build_async_client(
            _make_paged(chunk, limit=2),
            _make_paged(chunk2, limit=2),
            _empty_paged(),
        )

        df = asyncio.run(
            eql_query_to_dataframe("SELECT v FROM t", client, chunk_size=2)
        )

        assert list(df["v"]) == [1, 2, 3, 4]
        assert client.eql.get_paged_query_result.await_count == 3

    def test_parameters_propagated_to_request(self):
        client = _build_async_client(_empty_paged())

        asyncio.run(
            eql_query_to_dataframe(
                "SELECT * FROM t WHERE id = @id",
                client,
                chunk_size=500,
                columns={"name": "string"},
                ds="ds1",
                id_field="oid",
                parameters={"id": 42},
            )
        )

        call = client.eql.get_paged_query_result.await_args
        req = call.kwargs["body"]
        assert req.query == "SELECT * FROM t WHERE id = @id"
        assert req.limit == 500
        assert req.offset == 0
        assert req.columns == {"name": "string"}
        assert req.ds == "ds1"
        assert req.idField == "oid"
        assert req.parameters == {"id": 42}
        # DataFrame path forces with_geom=False -- we don't transfer geometry.
        assert req.withgeom is False

    def test_empty_properties_become_empty_row(self):
        # Features with empty/None properties shouldn't crash row extraction.
        features = [
            FeatureDc(properties={}, geometry=None),
            FeatureDc(properties={"k": "v"}, geometry=None),
        ]
        client = _build_async_client(_make_paged(features, limit=1000))

        df = asyncio.run(
            eql_query_to_dataframe("SELECT * FROM t", client, chunk_size=1000)
        )

        assert len(df) == 2


# ---------------------------------------------------------------------------
# eql_query_to_geodataframe
# ---------------------------------------------------------------------------


class TestEqlQueryToGeodataframe:
    """Tests for the async GeoDataFrame helper."""

    def test_single_page_returns_geodataframe(self):
        features = [
            _make_feature({"name": "A"}, x=30.0, y=10.0),
            _make_feature({"name": "B"}, x=31.0, y=11.0),
        ]
        client = _build_async_client(_make_paged(features, limit=1000))

        gdf = asyncio.run(
            eql_query_to_geodataframe(
                "SELECT * FROM t", client, chunk_size=1000, target_crs="EPSG:4326",
            )
        )

        assert len(gdf) == 2
        assert "geometry" in gdf.columns
        assert "name" in gdf.columns
        assert list(gdf["name"]) == ["A", "B"]
        client.eql.get_paged_query_result.assert_awaited_once()

    def test_empty_result_returns_empty_geodataframe(self):
        client = _build_async_client(_empty_paged())

        gdf = asyncio.run(
            eql_query_to_geodataframe(
                "SELECT * FROM t", client, chunk_size=1000, target_crs="EPSG:4326",
            )
        )

        assert len(gdf) == 0
        assert "geometry" in gdf.columns
        client.eql.get_paged_query_result.assert_awaited_once()

    def test_parameters_propagated_to_request(self):
        client = _build_async_client(_empty_paged())

        asyncio.run(
            eql_query_to_geodataframe(
                "SELECT * FROM t WHERE id = @id",
                client,
                chunk_size=250,
                columns={"name": "string"},
                ds="ds1",
                geometry_field="geom",
                id_field="oid",
                parameters={"id": 7},
                with_geom=True,
                target_crs="EPSG:3857",
            )
        )

        call = client.eql.get_paged_query_result.await_args
        req = call.kwargs["body"]
        assert req.query == "SELECT * FROM t WHERE id = @id"
        assert req.limit == 250
        assert req.offset == 0
        assert req.columns == {"name": "string"}
        assert req.ds == "ds1"
        assert req.geometryField == "geom"
        assert req.idField == "oid"
        assert req.parameters == {"id": 7}
        assert req.withgeom is True

    def test_with_geom_false_propagated(self):
        client = _build_async_client(_empty_paged())

        asyncio.run(
            eql_query_to_geodataframe(
                "SELECT * FROM t", client, with_geom=False,
            )
        )

        req = client.eql.get_paged_query_result.await_args.kwargs["body"]
        assert req.withgeom is False

    def test_multipage_pagination(self):
        chunk1 = [
            _make_feature({"v": 1}, x=0.0, y=0.0),
            _make_feature({"v": 2}, x=1.0, y=1.0),
        ]
        chunk2 = [
            _make_feature({"v": 3}, x=2.0, y=2.0),
            _make_feature({"v": 4}, x=3.0, y=3.0),
        ]
        client = _build_async_client(
            _make_paged(chunk1, limit=2),
            _make_paged(chunk2, limit=2),
            _empty_paged(),
        )

        gdf = asyncio.run(
            eql_query_to_geodataframe(
                "SELECT * FROM t", client, chunk_size=2, target_crs="EPSG:4326",
            )
        )

        assert len(gdf) == 4
        assert client.eql.get_paged_query_result.await_count == 3


# ---------------------------------------------------------------------------
# Error propagation
# ---------------------------------------------------------------------------


class TestErrorPropagation:
    """Backend errors must bubble up, not be swallowed into empty results."""

    def test_dataframe_propagates_backend_error(self):
        client = MagicMock()
        client.eql = MagicMock()
        client.eql.get_paged_query_result = AsyncMock(
            side_effect=RuntimeError("server boom")
        )

        with pytest.raises(RuntimeError, match="server boom"):
            asyncio.run(eql_query_to_dataframe("SELECT * FROM t", client))

    def test_geodataframe_propagates_backend_error(self):
        client = MagicMock()
        client.eql = MagicMock()
        client.eql.get_paged_query_result = AsyncMock(
            side_effect=RuntimeError("server boom")
        )

        with pytest.raises(RuntimeError, match="server boom"):
            asyncio.run(eql_query_to_geodataframe("SELECT * FROM t", client))


# ---------------------------------------------------------------------------
# eql_describe / geometry_field="auto"
# ---------------------------------------------------------------------------


def _make_columns(geom_name="geometry"):
    """Build a typical get_query_description result: string + geometry."""
    from evergis_api.schemas import (
        GeometryAttributeConfigurationDc,
        StringAttributeConfigurationDc,
    )

    return [
        StringAttributeConfigurationDc(attributeName="name", type="String"),
        GeometryAttributeConfigurationDc(attributeName=geom_name, type="Point"),
    ]


class TestAsyncEqlDescribe:
    """Tests for the async eql_describe helper and geometry_field='auto'."""

    def test_describe_is_coroutine_function(self):
        assert inspect.iscoroutinefunction(eql_describe)

    def test_describe_returns_friendly_columns(self):
        client = MagicMock()
        client.eql = MagicMock()
        client.eql.get_query_description = AsyncMock(return_value=_make_columns())

        cols = asyncio.run(eql_describe("SELECT * FROM t", client))

        by_name = {c["name"]: c for c in cols}
        assert by_name["geometry"]["is_geometry"] is True
        assert by_name["name"]["kind"] == "string"
        body = client.eql.get_query_description.await_args.kwargs["body"]
        assert body.query == "SELECT * FROM t"

    def test_auto_detects_geom_column(self):
        client = _build_async_client(_empty_paged())
        client.eql.get_query_description = AsyncMock(
            return_value=_make_columns("geom")
        )

        asyncio.run(
            eql_query_to_geodataframe("SELECT * FROM t", client, geometry_field="auto")
        )

        body = client.eql.get_paged_query_result.await_args.kwargs["body"]
        assert body.geometryField == "geom"

    def test_auto_falls_back_to_geometry_when_describe_fails(self):
        client = _build_async_client(_empty_paged())
        client.eql.get_query_description = AsyncMock(
            side_effect=RuntimeError("boom")
        )

        asyncio.run(
            eql_query_to_geodataframe("SELECT * FROM t", client, geometry_field="auto")
        )

        body = client.eql.get_paged_query_result.await_args.kwargs["body"]
        assert body.geometryField == "geometry"
