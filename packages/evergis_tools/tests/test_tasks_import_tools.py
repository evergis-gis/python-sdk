# -*- coding: utf-8 -*-
"""Tests for evergis_tools.tasks.import_tools -- unit, no network."""

import inspect
from unittest.mock import MagicMock, patch

import pytest

from evergis_tools.tasks.import_tools import (
    build_attribute_mappings_from_schema,
    get_csv_data_schema_rest,
    get_fgdb_data_schema_rest,
    get_gpkg_data_schema_rest,
    get_shapefile_data_schema_rest,
    get_xlsx_data_schema_rest,
    import_csv_to_layer,
    import_fgdb_to_layer,
    import_gpkg_to_layer,
    import_shapefile_to_layer,
    import_xlsx_to_layer,
)


IMPORT_FUNCS = [
    ("import_csv_to_layer", import_csv_to_layer),
    ("import_xlsx_to_layer", import_xlsx_to_layer),
    ("import_shapefile_to_layer", import_shapefile_to_layer),
    ("import_gpkg_to_layer", import_gpkg_to_layer),
    ("import_fgdb_to_layer", import_fgdb_to_layer),
]

COMMON_PARAMS = [
    "client",
    "source_file_name",
    "target_layer",
    "target_layer_parent_path",
    "attribute_mapping",
    "attribute_type_mapping",
    "progress_callback",
    "defer",
    "timeout",
    "check_interval",
]


class TestImportSignatures:
    """All import-to-layer entrypoints expose the same option set."""

    @pytest.mark.parametrize("name,func", IMPORT_FUNCS)
    def test_importable(self, name, func):
        assert callable(func), f"{name} is not callable"

    @pytest.mark.parametrize("name,func", IMPORT_FUNCS)
    @pytest.mark.parametrize("param", COMMON_PARAMS)
    def test_has_common_param(self, name, func, param):
        sig = inspect.signature(func)
        assert param in sig.parameters, (
            f"{name} is missing parameter {param!r}"
        )


SCHEMA_FUNCS = [
    ("get_csv_data_schema_rest", get_csv_data_schema_rest),
    ("get_xlsx_data_schema_rest", get_xlsx_data_schema_rest),
    ("get_shapefile_data_schema_rest", get_shapefile_data_schema_rest),
    ("get_gpkg_data_schema_rest", get_gpkg_data_schema_rest),
    ("get_fgdb_data_schema_rest", get_fgdb_data_schema_rest),
]


class TestSchemaDiscovery:
    """get_*_data_schema_rest helpers post to remotetaskmanager."""

    @pytest.mark.parametrize("name,func", SCHEMA_FUNCS)
    def test_importable(self, name, func):
        assert callable(func), f"{name} is not callable"

    @pytest.mark.parametrize("name,func", SCHEMA_FUNCS)
    def test_signature_has_client_and_resource_id(self, name, func):
        sig = inspect.signature(func)
        assert "client" in sig.parameters
        assert "resource_id" in sig.parameters

    @pytest.mark.parametrize("name,func,expected_type", [
        ("get_csv_data_schema_rest", get_csv_data_schema_rest, "csv"),
        ("get_xlsx_data_schema_rest", get_xlsx_data_schema_rest, "xlsx"),
        ("get_gpkg_data_schema_rest", get_gpkg_data_schema_rest, "gpkg"),
        ("get_fgdb_data_schema_rest", get_fgdb_data_schema_rest, "gdb"),
    ])
    def test_calls_remotetaskmanager_with_source_type(
        self, name, func, expected_type
    ):
        client = MagicMock()
        resource = MagicMock()
        resource.resourceId = "res-abc"
        with patch(
            "evergis_tools.tasks.import_tools.get_info.resolve_resource",
            return_value=resource,
        ):
            func(client, "em:Projects/file")

        assert client.remotetaskmanager.post.called
        payload = client.remotetaskmanager.post.call_args.kwargs["body"]
        assert payload.workerType == "importExport"
        assert payload.methodType == "importExport/dataSchema"
        assert payload.data["source_fileName"] == "res-abc"
        assert payload.data["source_type"] == expected_type

    def test_shapefile_omits_source_type(self):
        # Shapefile helper does not set source_type (server infers it).
        client = MagicMock()
        resource = MagicMock()
        resource.resourceId = "res-shp"
        with patch(
            "evergis_tools.tasks.import_tools.get_info.resolve_resource",
            return_value=resource,
        ):
            get_shapefile_data_schema_rest(client, "em:Projects/file.zip")

        payload = client.remotetaskmanager.post.call_args.kwargs["body"]
        assert payload.data == {"source_fileName": "res-shp"}


def _make_schema(attrs, layer_name="layer1"):
    return {
        "layers": [
            {
                "name": layer_name,
                "attributesConfiguration": {"attributes": attrs},
            }
        ]
    }


class TestBuildAttributeMappings:
    """build_attribute_mappings_from_schema unpacks dataSchema responses."""

    def test_identity_attribute_mapping(self):
        schema = _make_schema([
            {"attributeName": "name", "type": "String"},
            {"attributeName": "pop", "type": "Int32"},
        ])
        attr_map, type_map = build_attribute_mappings_from_schema(schema)
        assert attr_map == {"name": "name", "pop": "pop"}
        assert type_map == {"name": "String", "pop": "Int32"}

    def test_includes_geometry_by_default(self):
        schema = _make_schema([
            {"attributeName": "geom", "type": "Point",
             "attributeConfigurationType": "Geometry"},
            {"attributeName": "name", "type": "String"},
        ])
        attr_map, type_map = build_attribute_mappings_from_schema(schema)
        assert "geom" in attr_map
        assert type_map["geom"] == "Point"

    def test_exclude_geometry(self):
        schema = _make_schema([
            {"attributeName": "geom", "type": "Point",
             "attributeConfigurationType": "Geometry"},
            {"attributeName": "name", "type": "String"},
        ])
        attr_map, type_map = build_attribute_mappings_from_schema(
            schema, include_geometry=False
        )
        assert "geom" not in attr_map
        assert "geom" not in type_map
        assert attr_map == {"name": "name"}

    def test_pick_layer_by_name(self):
        schema = {
            "layers": [
                {
                    "name": "a",
                    "attributesConfiguration": {
                        "attributes": [{"attributeName": "x", "type": "String"}]
                    },
                },
                {
                    "name": "b",
                    "attributesConfiguration": {
                        "attributes": [{"attributeName": "y", "type": "Int32"}]
                    },
                },
            ]
        }
        attr_map, type_map = build_attribute_mappings_from_schema(
            schema, layer_name="b"
        )
        assert attr_map == {"y": "y"}
        assert type_map == {"y": "Int32"}

    def test_unknown_layer_raises(self):
        schema = _make_schema([{"attributeName": "x", "type": "String"}])
        with pytest.raises(ValueError, match="not found"):
            build_attribute_mappings_from_schema(schema, layer_name="missing")

    def test_empty_schema_raises(self):
        with pytest.raises(ValueError, match="no layers"):
            build_attribute_mappings_from_schema({"layers": []})

    def test_skips_entries_without_attribute_name(self):
        schema = _make_schema([
            {"attributeName": "ok", "type": "String"},
            {"type": "String"},  # missing attributeName -> skipped
        ])
        attr_map, type_map = build_attribute_mappings_from_schema(schema)
        assert attr_map == {"ok": "ok"}
        assert type_map == {"ok": "String"}


class TestImportFunctionsRunTask:
    """Full mocked round-trip: import_* builds a prototype and calls run_task."""

    def _patch_module(self, module_path):
        """Patch resolve_resource, resolve_target_layer_parent, run_task."""
        source_resource = MagicMock()
        source_resource.resourceId = "src-resource-id"
        return patch.multiple(
            module_path,
            resolve_resource=MagicMock(return_value=source_resource),
            resolve_target_layer_parent=MagicMock(return_value="parent-folder-id"),
            run_task=MagicMock(return_value="task-result"),
        )

    def test_import_csv_to_layer_builds_prototype(self):
        client = MagicMock()
        module = "evergis_tools.tasks.import_tools.csv_import_to_layer"
        with self._patch_module(module):
            import evergis_tools.tasks.import_tools.csv_import_to_layer as m
            result = import_csv_to_layer(
                client,
                source_file_name="em:src.csv",
                target_layer="em.evg_csv_demo",
                target_layer_parent_path="em:Projects/results",
                column_delimiter=",",
                attribute_mapping={"name": "name"},
                attribute_type_mapping={"name": "String"},
            )
            assert result == "task-result"
            assert m.run_task.called
            prototype = m.run_task.call_args.kwargs["prototype"]
            start_params = prototype.subTaskSettings[0].startParameters
            assert start_params["source_fileName"] == "src-resource-id"
            assert start_params["source_columnDelimiter"] == ","
            # target_layer holds the layer reference config
            target = start_params.get("target_layer") or start_params.get("target")
            assert target is not None
            # find name/parentId regardless of nesting
            flat = str(target)
            assert "em.evg_csv_demo" in flat
            assert "parent-folder-id" in flat

    def test_import_gpkg_to_layer_builds_prototype(self):
        client = MagicMock()
        module = "evergis_tools.tasks.import_tools.gpkg_import_to_layer"
        with self._patch_module(module):
            import evergis_tools.tasks.import_tools.gpkg_import_to_layer as m
            result = import_gpkg_to_layer(
                client,
                source_file_name="em:Projects/file.gpkg",
                source_layer_name="countries",
                target_layer="em.evg_gpkg_countries",
                target_layer_parent_path="em:Projects/results",
            )
            assert result == "task-result"
            assert m.run_task.called
            prototype = m.run_task.call_args.kwargs["prototype"]
            start_params = prototype.subTaskSettings[0].startParameters
            assert start_params["source_fileName"] == "src-resource-id"
            assert start_params["source_layerName"] == "countries"
            assert "em.evg_gpkg_countries" in str(start_params)

    def test_import_gpkg_to_layer_defer_returns_taskstep(self):
        from evergis_tools.tasks.pipeline import TaskStep

        client = MagicMock()
        module = "evergis_tools.tasks.import_tools.gpkg_import_to_layer"
        with self._patch_module(module):
            import evergis_tools.tasks.import_tools.gpkg_import_to_layer as m
            result = import_gpkg_to_layer(
                client,
                source_file_name="em:Projects/file.gpkg",
                source_layer_name="countries",
                target_layer="em.evg_gpkg_countries",
                defer=True,
            )
            assert isinstance(result, TaskStep)
            assert result.task_type == "importExport"
            # defer must skip run_task
            assert not m.run_task.called

    def test_import_gpkg_requires_source_layer_name(self):
        client = MagicMock()
        with pytest.raises(ValueError, match="source_layer_name"):
            import_gpkg_to_layer(
                client,
                source_file_name="em:file.gpkg",
                source_layer_name="",
                target_layer="em.evg_x",
            )
