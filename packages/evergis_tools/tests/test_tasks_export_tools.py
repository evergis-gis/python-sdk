# -*- coding: utf-8 -*-
"""Tests for evergis_tools.tasks.export_tools - unit, no network."""

import inspect
from unittest.mock import MagicMock, patch

import pytest

from evergis_tools.tasks.export_tools import (
    export_layer_to_csv,
    export_layer_to_geojson,
    export_layer_to_gpkg,
    export_layer_to_shapefile,
    export_layer_to_xlsx,
)
from evergis_tools.tasks.pipeline import TaskStep


EXPORT_FUNCS = [
    ("csv", export_layer_to_csv),
    ("geojson", export_layer_to_geojson),
    ("gpkg", export_layer_to_gpkg),
    ("shapefile", export_layer_to_shapefile),
    ("xlsx", export_layer_to_xlsx),
]

COMMON_PARAMS = {
    "client",
    "source_layer",
    "target_file_name",
    "attribute_mapping",
    "defer",
    "timeout",
}


class TestExportSignatures:
    """All 5 export functions share a common surface."""

    @pytest.mark.parametrize("name,func", EXPORT_FUNCS)
    def test_imports(self, name, func):
        assert callable(func)
        assert func.__name__ == f"export_layer_to_{name}"

    @pytest.mark.parametrize("name,func", EXPORT_FUNCS)
    def test_common_params_present(self, name, func):
        params = set(inspect.signature(func).parameters)
        missing = COMMON_PARAMS - params
        assert not missing, f"{name}: missing {missing}"

    @pytest.mark.parametrize("name,func", EXPORT_FUNCS)
    def test_default_defer_false(self, name, func):
        assert inspect.signature(func).parameters["defer"].default is False

    @pytest.mark.parametrize("name,func", EXPORT_FUNCS)
    def test_default_wait_for_completion_true(self, name, func):
        assert inspect.signature(func).parameters["wait_for_completion"].default is True

    @pytest.mark.parametrize("name,func", EXPORT_FUNCS)
    def test_default_timeout_300(self, name, func):
        assert inspect.signature(func).parameters["timeout"].default == 300

    @pytest.mark.parametrize("name,func", EXPORT_FUNCS)
    def test_default_check_interval_2(self, name, func):
        assert inspect.signature(func).parameters["check_interval"].default == 2.0

    @pytest.mark.parametrize("name,func", EXPORT_FUNCS)
    def test_default_target_parent_path_none(self, name, func):
        assert inspect.signature(func).parameters["target_parent_path"].default is None

    @pytest.mark.parametrize("name,func", EXPORT_FUNCS)
    def test_source_layer_required(self, name, func):
        # No default -> required keyword-only argument
        param = inspect.signature(func).parameters["source_layer"]
        assert param.default is inspect.Parameter.empty

    @pytest.mark.parametrize("name,func", EXPORT_FUNCS)
    def test_target_file_name_required(self, name, func):
        param = inspect.signature(func).parameters["target_file_name"]
        assert param.default is inspect.Parameter.empty


class TestExportLayerToCsvBehaviour:
    """Behaviour of export_layer_to_csv (representative for the family)."""

    def test_empty_source_layer_raises(self):
        with pytest.raises(ValueError, match="source_layer"):
            export_layer_to_csv(
                MagicMock(),
                source_layer="",
                target_file_name="out.csv",
            )

    def test_empty_target_file_name_raises(self):
        with pytest.raises(ValueError, match="target_file_name"):
            export_layer_to_csv(
                MagicMock(),
                source_layer="em.layer",
                target_file_name="",
            )

    def test_defer_returns_task_step(self):
        client = MagicMock()
        with patch(
            "evergis_tools.tasks.export_tools.export_layer_to_csv.resolve_resource"
        ) as resolve:
            resolve.return_value = MagicMock(resourceId="rid-1")
            step = export_layer_to_csv(
                client,
                source_layer="em.layer",
                target_file_name="em:Projects/out.csv",
                defer=True,
            )
        assert isinstance(step, TaskStep)
        assert step.task_type == "importExport"
        assert step.start_parameters["target_fileName"] == "rid-1"
        assert step.start_parameters["target_type"] == "csv"

    def test_target_parent_path_skips_target_resolve(self):
        client = MagicMock()
        with patch(
            "evergis_tools.tasks.export_tools.export_layer_to_csv.resolve_resource"
        ) as resolve:
            resolve.return_value = MagicMock(resourceId="folder-id")
            step = export_layer_to_csv(
                client,
                source_layer="em.layer",
                target_file_name="out.csv",
                target_parent_path="em:Exports",
                defer=True,
            )
        # Only one call: parent folder resolve. target_file_name is used as-is.
        assert resolve.call_count == 1
        assert step.start_parameters["target_fileName"] == "out.csv"

    def test_source_eql_branch(self):
        """source_eql sets eql, no layerName / condition."""
        with patch(
            "evergis_tools.tasks.export_tools.export_layer_to_csv.resolve_resource"
        ) as resolve:
            resolve.return_value = MagicMock(resourceId="rid")
            step = export_layer_to_csv(
                MagicMock(),
                source_layer="em.layer",
                source_eql="SELECT * FROM em.layer WHERE x > 1",
                target_file_name="out.csv",
                defer=True,
            )
        src = step.start_parameters["source_layer"]
        assert src.get("eql") == "SELECT * FROM em.layer WHERE x > 1"
        assert "layerName" not in src
        assert "condition" not in src

    def test_source_layer_condition_branch(self):
        """No eql -> layerName + condition populated."""
        with patch(
            "evergis_tools.tasks.export_tools.export_layer_to_csv.resolve_resource"
        ) as resolve:
            resolve.return_value = MagicMock(resourceId="rid")
            step = export_layer_to_csv(
                MagicMock(),
                source_layer="em.layer",
                source_layer_condition="x > 1",
                target_file_name="out.csv",
                defer=True,
            )
        src = step.start_parameters["source_layer"]
        assert src.get("layerName") == "em.layer"
        assert src.get("condition") == "x > 1"
        assert "eql" not in src

    def test_non_defer_calls_run_task(self):
        """When defer=False, create_task_prototype + run_task are invoked."""
        sentinel = object()
        with patch(
            "evergis_tools.tasks.export_tools.export_layer_to_csv.resolve_resource"
        ) as resolve, patch(
            "evergis_tools.tasks.export_tools.export_layer_to_csv.create_task_prototype"
        ) as create_proto, patch(
            "evergis_tools.tasks.export_tools.export_layer_to_csv.run_task"
        ) as run:
            resolve.return_value = MagicMock(resourceId="rid")
            create_proto.return_value = MagicMock(name="prototype")
            run.return_value = sentinel

            result = export_layer_to_csv(
                MagicMock(),
                source_layer="em.layer",
                target_file_name="em:Exports/out.csv",
            )

        assert result is sentinel
        assert create_proto.call_count == 1
        assert create_proto.call_args.args[0] == "importExport:importExport"
        assert run.call_count == 1


class TestExportLayerToShapefileBranches:
    """source_eql vs source_layer_condition for shapefile."""

    def test_source_eql(self):
        with patch(
            "evergis_tools.tasks.export_tools.export_layer_to_shapefile.resolve_resource"
        ) as resolve:
            resolve.return_value = MagicMock(resourceId="rid")
            step = export_layer_to_shapefile(
                MagicMock(),
                source_layer="em.layer",
                source_eql="SELECT * FROM em.layer",
                target_file_name="out.shp",
                defer=True,
            )
        assert step.start_parameters["source_layer"].get("eql")
        assert "layerName" not in step.start_parameters["source_layer"]

    def test_source_layer_condition(self):
        with patch(
            "evergis_tools.tasks.export_tools.export_layer_to_shapefile.resolve_resource"
        ) as resolve:
            resolve.return_value = MagicMock(resourceId="rid")
            step = export_layer_to_shapefile(
                MagicMock(),
                source_layer="em.layer",
                source_layer_condition="id < 100",
                target_file_name="out.shp",
                defer=True,
            )
        src = step.start_parameters["source_layer"]
        assert src.get("layerName") == "em.layer"
        assert src.get("condition") == "id < 100"

    def test_target_layer_name_propagates(self):
        """Shapefile DOES forward target_layer_name to startParameters."""
        with patch(
            "evergis_tools.tasks.export_tools.export_layer_to_shapefile.resolve_resource"
        ) as resolve:
            resolve.return_value = MagicMock(resourceId="rid")
            step = export_layer_to_shapefile(
                MagicMock(),
                source_layer="em.layer",
                target_file_name="out.shp",
                target_layer_name="custom_layer",
                defer=True,
            )
        # by_alias dump -> flat target_layerName key
        assert step.start_parameters.get("target_layerName") == "custom_layer"


class TestExportLayerToGpkgBug:
    """Documents the known bug: target_layer_name is accepted but ignored."""

    def test_target_layer_name_accepted_in_signature(self):
        # The parameter exists and has a default of None.
        sig = inspect.signature(export_layer_to_gpkg)
        assert "target_layer_name" in sig.parameters
        assert sig.parameters["target_layer_name"].default is None

    def test_target_layer_name_not_in_start_parameters(self):
        """The commented-out target_layerName=... means the value is dropped silently.

        This pins current behaviour so we notice if/when the bug is fixed.
        """
        with patch(
            "evergis_tools.tasks.export_tools.export_layer_to_gpkg.resolve_resource"
        ) as resolve:
            resolve.return_value = MagicMock(resourceId="rid")
            step = export_layer_to_gpkg(
                MagicMock(),
                source_layer="em.layer",
                target_file_name="out.gpkg",
                target_layer_name="my_custom_name",
                defer=True,
            )
        # The custom layer name should NOT appear in dumped params - the
        # target_layerName=target_layer_name line is commented out in source.
        assert "target_layerName" not in step.start_parameters
        assert "my_custom_name" not in str(step.start_parameters)
