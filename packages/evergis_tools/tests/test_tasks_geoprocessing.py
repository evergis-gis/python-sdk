# -*- coding: utf-8 -*-
"""Tests for evergis_tools.tasks.geoprocessing -- unit, no network."""

from unittest.mock import MagicMock, patch

import pytest

from evergis_tools.tasks.geoprocessing import (
    copy_layer_via_eql,
    delete_from_layer_via_eql,
    fix_layer_geometry,
    union_layers_via_eql,
    update_layer_via_eql,
    validate_layer_geometry,
)
from evergis_tools.tasks.pipeline import TaskStep


# ---------------------------------------------------------------------------
# Fixtures
# ---------------------------------------------------------------------------


@pytest.fixture
def client():
    return MagicMock()


@pytest.fixture(autouse=True)
def stub_resolve_target_layer_parent():
    """Prevent network calls in copy/union which resolve catalog folders."""
    with patch(
        "evergis_tools.tasks.geoprocessing.copy_layer_via_eql.resolve_target_layer_parent",
        return_value=None,
    ) as p_copy, patch(
        "evergis_tools.tasks.geoprocessing.union_layers_via_eql.resolve_target_layer_parent",
        return_value=None,
    ) as p_union:
        yield (p_copy, p_union)


# ---------------------------------------------------------------------------
# Imports
# ---------------------------------------------------------------------------


class TestGeoprocessingImports:
    def test_all_six_callable(self):
        assert callable(copy_layer_via_eql)
        assert callable(update_layer_via_eql)
        assert callable(delete_from_layer_via_eql)
        assert callable(union_layers_via_eql)
        assert callable(validate_layer_geometry)
        assert callable(fix_layer_geometry)


# ---------------------------------------------------------------------------
# copy_layer_via_eql
# ---------------------------------------------------------------------------


class TestCopyLayerViaEql:
    def test_defer_returns_taskstep_geoprocessing(self, client):
        step = copy_layer_via_eql(
            client=client,
            eql="SELECT * FROM src",
            target_layer="tgt",
            defer=True,
        )
        assert isinstance(step, TaskStep)
        assert step.task_type == "geoProcessing"

    def test_source_eql_and_target_in_params(self, client):
        step = copy_layer_via_eql(
            client=client,
            eql="SELECT * FROM src",
            target_layer="tgt_layer",
            source_condition="status = 'ok'",
            defer=True,
        )
        sp = step.start_parameters
        assert sp["proccessingType"] == "copy"
        assert sp["sourceLayer"]["eql"] == "SELECT * FROM src"
        assert sp["sourceLayer"]["condition"] == "status = 'ok'"
        assert sp["targetLayer"]["name"] == "tgt_layer"

    def test_empty_eql_raises(self, client):
        with pytest.raises(ValueError, match="eql"):
            copy_layer_via_eql(client=client, eql="", target_layer="tgt", defer=True)

    def test_empty_target_layer_raises(self, client):
        with pytest.raises(ValueError, match="target_layer"):
            copy_layer_via_eql(
                client=client, eql="SELECT 1", target_layer="", defer=True
            )

    def test_run_task_invoked_when_not_deferred(self, client):
        with patch(
            "evergis_tools.tasks.geoprocessing.copy_layer_via_eql.run_task"
        ) as mock_run:
            mock_run.return_value = "result"
            out = copy_layer_via_eql(
                client=client, eql="SELECT 1", target_layer="tgt"
            )
            mock_run.assert_called_once()
            assert out == "result"


# ---------------------------------------------------------------------------
# update_layer_via_eql
# ---------------------------------------------------------------------------


class TestUpdateLayerViaEql:
    def test_defer_returns_taskstep_geoprocessing(self, client):
        step = update_layer_via_eql(
            client=client,
            eql="SELECT * FROM src",
            target_layer="tgt",
            defer=True,
        )
        assert isinstance(step, TaskStep)
        assert step.task_type == "geoProcessing"

    def test_cached_default_true_materializes(self, client):
        step = update_layer_via_eql(
            client=client,
            eql="SELECT * FROM src",
            target_layer="tgt",
            defer=True,
        )
        # cached=True -> materializedView=True serialized via alias
        assert step.start_parameters["materializedView"] is True
        assert step.start_parameters["proccessingType"] == "update"

    def test_cached_false_materializes_false(self, client):
        step = update_layer_via_eql(
            client=client,
            eql="SELECT * FROM src",
            target_layer="tgt",
            cached=False,
            defer=True,
        )
        assert step.start_parameters["materializedView"] is False

    def test_empty_eql_raises(self, client):
        with pytest.raises(ValueError, match="eql"):
            update_layer_via_eql(
                client=client, eql="", target_layer="tgt", defer=True
            )

    def test_empty_target_layer_raises(self, client):
        with pytest.raises(ValueError, match="target_layer"):
            update_layer_via_eql(
                client=client, eql="SELECT 1", target_layer="", defer=True
            )


# ---------------------------------------------------------------------------
# delete_from_layer_via_eql
# ---------------------------------------------------------------------------


class TestDeleteFromLayerViaEql:
    def test_defer_returns_taskstep_delete(self, client):
        # Delete is the only one using task_type="delete", not "geoProcessing".
        step = delete_from_layer_via_eql(
            client=client,
            eql="SELECT * FROM src WHERE expired",
            target_layer="tgt",
            defer=True,
        )
        assert isinstance(step, TaskStep)
        assert step.task_type == "delete"

    def test_source_and_target_in_params(self, client):
        step = delete_from_layer_via_eql(
            client=client,
            eql="SELECT * FROM src WHERE expired",
            target_layer="tgt",
            defer=True,
        )
        sp = step.start_parameters
        assert sp["sourceLayer"]["eql"] == "SELECT * FROM src WHERE expired"
        assert sp["targetLayer"]["name"] == "tgt"

    def test_empty_eql_raises(self, client):
        with pytest.raises(ValueError, match="eql"):
            delete_from_layer_via_eql(
                client=client, eql="", target_layer="tgt", defer=True
            )

    def test_empty_target_layer_raises(self, client):
        with pytest.raises(ValueError, match="target_layer"):
            delete_from_layer_via_eql(
                client=client, eql="SELECT 1", target_layer="", defer=True
            )

    def test_run_task_invoked_when_not_deferred(self, client):
        with patch(
            "evergis_tools.tasks.geoprocessing.delete_from_layer_via_eql.run_task"
        ) as mock_run:
            mock_run.return_value = "result"
            delete_from_layer_via_eql(
                client=client, eql="SELECT 1", target_layer="tgt"
            )
            mock_run.assert_called_once()


# ---------------------------------------------------------------------------
# union_layers_via_eql
# ---------------------------------------------------------------------------


class TestUnionLayersViaEql:
    def test_defer_returns_taskstep_geoprocessing(self, client):
        # task_type is stored as "geoProcessing" in defer payload,
        # but prototype path uses "geoProcessing:union".
        step = union_layers_via_eql(
            client=client,
            eql="SELECT * FROM src",
            target_layer="tgt",
            defer=True,
        )
        assert isinstance(step, TaskStep)
        assert step.task_type == "geoProcessing"

    def test_group_attribute_propagates(self, client):
        step = union_layers_via_eql(
            client=client,
            eql="SELECT * FROM src",
            target_layer="tgt",
            group_attribute="region_id",
            defer=True,
        )
        sp = step.start_parameters
        assert sp["groupAttribute"] == "region_id"
        assert sp["sourceLayer"]["eql"] == "SELECT * FROM src"
        assert sp["targetLayer"]["name"] == "tgt"

    def test_group_attribute_omitted_when_none(self, client):
        step = union_layers_via_eql(
            client=client,
            eql="SELECT * FROM src",
            target_layer="tgt",
            defer=True,
        )
        # exclude_none=True -> the key is absent
        assert "groupAttribute" not in step.start_parameters

    def test_empty_eql_raises(self, client):
        with pytest.raises(ValueError, match="eql"):
            union_layers_via_eql(
                client=client, eql="", target_layer="tgt", defer=True
            )

    def test_empty_target_layer_raises(self, client):
        with pytest.raises(ValueError, match="target_layer"):
            union_layers_via_eql(
                client=client, eql="SELECT 1", target_layer="", defer=True
            )

    def test_prototype_uses_union_subtype(self, client):
        # Hit run_task path to confirm the "geoProcessing:union" task_type
        # is what create_task_prototype is called with.
        with patch(
            "evergis_tools.tasks.geoprocessing.union_layers_via_eql.create_task_prototype"
        ) as mock_proto, patch(
            "evergis_tools.tasks.geoprocessing.union_layers_via_eql.run_task"
        ) as mock_run:
            mock_run.return_value = "result"
            union_layers_via_eql(
                client=client, eql="SELECT 1", target_layer="tgt"
            )
            mock_proto.assert_called_once()
            assert mock_proto.call_args.args[0] == "geoProcessing:union"


# ---------------------------------------------------------------------------
# validate_layer_geometry
# ---------------------------------------------------------------------------


class TestValidateLayerGeometry:
    def test_defer_returns_taskstep_geoprocessing(self, client):
        step = validate_layer_geometry(
            client=client,
            source_layer="buildings",
            target_layer="invalid_buildings",
            defer=True,
        )
        assert isinstance(step, TaskStep)
        assert step.task_type == "geoProcessing"

    def test_layer_name_branch(self, client):
        # No SELECT/FROM -> treated as layer name.
        step = validate_layer_geometry(
            client=client,
            source_layer="buildings",
            target_layer="invalid_buildings",
            defer=True,
        )
        sp = step.start_parameters
        assert sp["sourceLayer"].get("layerName") == "buildings"
        assert "eql" not in sp["sourceLayer"]

    def test_eql_branch(self, client):
        step = validate_layer_geometry(
            client=client,
            source_layer="SELECT * FROM roads WHERE status='new'",
            target_layer="invalid_roads",
            defer=True,
        )
        sp = step.start_parameters
        assert sp["sourceLayer"].get("eql") == "SELECT * FROM roads WHERE status='new'"
        assert "layerName" not in sp["sourceLayer"]

    def test_defaults(self, client):
        step = validate_layer_geometry(
            client=client,
            source_layer="buildings",
            target_layer="invalid_buildings",
            defer=True,
        )
        sp = step.start_parameters
        assert sp["proccessingType"] == "validateGeometry"
        assert sp["invalidReasonColumn"] == "validation_error"
        assert sp["baseObjectIdAttributeName"] == "source_object_id"
        # materialized_view default False -> alias serialized
        assert sp.get("materializedView") is False

    def test_custom_column_names(self, client):
        step = validate_layer_geometry(
            client=client,
            source_layer="buildings",
            target_layer="invalid_buildings",
            invalid_reason_column="err_desc",
            base_object_id_attribute="src_oid",
            defer=True,
        )
        sp = step.start_parameters
        assert sp["invalidReasonColumn"] == "err_desc"
        assert sp["baseObjectIdAttributeName"] == "src_oid"

    def test_empty_source_layer_raises(self, client):
        with pytest.raises(ValueError, match="source_layer"):
            validate_layer_geometry(
                client=client, source_layer="", target_layer="tgt", defer=True
            )

    def test_empty_target_layer_raises(self, client):
        with pytest.raises(ValueError, match="target_layer"):
            validate_layer_geometry(
                client=client, source_layer="buildings", target_layer="", defer=True
            )

    def test_default_timeout_300(self, client):
        # timeout default = 300; confirm by inspecting run_task call.
        with patch(
            "evergis_tools.tasks.geoprocessing.validate_layer_geometry.run_task"
        ) as mock_run:
            mock_run.return_value = "result"
            validate_layer_geometry(
                client=client, source_layer="buildings", target_layer="tgt"
            )
            assert mock_run.call_args.kwargs["timeout"] == 300


# ---------------------------------------------------------------------------
# fix_layer_geometry
# ---------------------------------------------------------------------------


class TestFixLayerGeometry:
    def test_defer_returns_taskstep_geoprocessing(self, client):
        step = fix_layer_geometry(
            client=client, layer_name="buildings", defer=True
        )
        assert isinstance(step, TaskStep)
        assert step.task_type == "geoProcessing"

    def test_only_target_layer_in_params(self, client):
        step = fix_layer_geometry(
            client=client, layer_name="buildings", defer=True
        )
        sp = step.start_parameters
        assert sp["targetLayer"]["name"] == "buildings"
        # No sourceLayer / eql for fixGeometry.
        assert "sourceLayer" not in sp
        assert "eql" not in sp

    def test_empty_layer_name_raises(self, client):
        with pytest.raises(ValueError, match="layer_name"):
            fix_layer_geometry(client=client, layer_name="", defer=True)

    def test_default_timeout_600(self, client):
        with patch(
            "evergis_tools.tasks.geoprocessing.fix_layer_geometry.run_task"
        ) as mock_run:
            mock_run.return_value = "result"
            fix_layer_geometry(client=client, layer_name="buildings")
            assert mock_run.call_args.kwargs["timeout"] == 600

    def test_prototype_uses_fixgeometry_subtype(self, client):
        with patch(
            "evergis_tools.tasks.geoprocessing.fix_layer_geometry.create_task_prototype"
        ) as mock_proto, patch(
            "evergis_tools.tasks.geoprocessing.fix_layer_geometry.run_task"
        ) as mock_run:
            mock_run.return_value = "result"
            fix_layer_geometry(client=client, layer_name="buildings")
            mock_proto.assert_called_once()
            assert mock_proto.call_args.args[0] == "geoProcessing:fixGeometry"
