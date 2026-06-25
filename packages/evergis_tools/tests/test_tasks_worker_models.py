# -*- coding: utf-8 -*-
"""Tests for tasks.worker_models - structural integrity and helpers.

worker_models is auto-generated, so we test the public surface and
the hand-rolled helpers (factories, conditional dispatch), not every
individual generated class.
"""

import re
from pathlib import Path

import pytest
from pydantic import BaseModel

from evergis_api.schemas import TaskPrototypeDto, SubTaskSettingsDto

from evergis_tools.tasks.worker_models import (
    BaseStartParameters,
    LayerReferenceConfig,
    SourceEqlConfig,
    ProvidernameType,
    ActionType,
    ModelType,
    SourceTypeType,
    TargetTypeType,
    OperationType,
    NetengineRouteStartParameters,
    create_start_parameters,
    create_task_prototype,
)
from evergis_tools.tasks.worker_models import importexport_conditional as iec
from evergis_tools.tasks.worker_models.importexport_conditional import (
    BaseImportexportStartParameters,
    CsvToLayerStartParameters,
    ImportexportSourceCsvTargetLayerStartParameters,
)


# Repo-root-relative path to the source dir, used by static grep tests.
_WORKER_MODELS_DIR = (
    Path(__file__).resolve().parents[1]
    / "evergis_tools"
    / "tasks"
    / "worker_models"
)


class TestBaseTypes:
    """Base Pydantic types used across all generated StartParameters."""

    def test_base_start_parameters_is_empty_model(self):
        assert issubclass(BaseStartParameters, BaseModel)
        # No declared fields - it's a marker base class.
        assert BaseStartParameters.model_fields == {}
        # Instantiable with no args.
        instance = BaseStartParameters()
        assert isinstance(instance, BaseStartParameters)

    def test_layer_reference_config_fields(self):
        fields = LayerReferenceConfig.model_fields
        assert set(fields.keys()) == {"name", "alias", "parentId"}
        # name is required.
        assert fields["name"].is_required()
        # alias and parentId are optional.
        assert not fields["alias"].is_required()
        assert not fields["parentId"].is_required()

    def test_layer_reference_config_construction(self):
        ref = LayerReferenceConfig(name="x")
        assert ref.name == "x"
        assert ref.alias is None
        assert ref.parentId is None

    def test_layer_reference_config_requires_name(self):
        with pytest.raises(Exception):
            LayerReferenceConfig()

    def test_source_eql_config_fields(self):
        fields = SourceEqlConfig.model_fields
        assert set(fields.keys()) == {
            "layer_name",
            "eql",
            "condition",
            "id_attribute",
            "geometry_attribute",
        }
        # All fields are optional.
        for fname, finfo in fields.items():
            assert not finfo.is_required(), f"{fname} must be optional"

    def test_source_eql_config_construction(self):
        cfg = SourceEqlConfig(layer_name="schema.layer", eql="SELECT 1")
        assert cfg.layer_name == "schema.layer"
        assert cfg.eql == "SELECT 1"
        assert cfg.condition is None

    def test_populate_by_name_accepts_python_name(self):
        # python_name path: layer_name=...
        cfg = SourceEqlConfig(layer_name="foo")
        assert cfg.layer_name == "foo"

    def test_populate_by_name_accepts_alias(self):
        # alias path: layerName=...
        cfg = SourceEqlConfig(layerName="foo", idAttribute="id")
        assert cfg.layer_name == "foo"
        assert cfg.id_attribute == "id"


class TestEnums:
    """Enum values must match server contract exactly."""

    def test_providername_type_has_expected_members(self):
        # These exact members are referenced in tutorials/examples.
        assert ProvidernameType.SPROUTE_ISOCHRONE_PEDESTRIAN.value == (
            "sproute_isochrone_pedestrian"
        )
        assert ProvidernameType.SPROUTE_ISOCHRONE_CAR_IN.value == (
            "sproute_isochrone_car_in"
        )
        assert ProvidernameType.SPROUTE_ISOCHRONE_CAR_OUT.value == (
            "sproute_isochrone_car_out"
        )
        assert ProvidernameType.OSRM_CAR.value == "osrm_car"
        assert ProvidernameType.OSRM_WALK.value == "osrm_walk"

    def test_providername_is_str_enum(self):
        # Inheriting str matters for JSON serialization.
        assert issubclass(ProvidernameType, str)

    def test_action_type_has_messaging_members(self):
        names = {m.name for m in ActionType}
        # Spot-check core members.
        assert "SEND_MESSAGE" in names
        assert "EDIT_MESSAGE" in names
        assert "DELETE_MESSAGE" in names
        assert "CREATE_CHANNEL" in names

    def test_model_type_has_pro_and_simple(self):
        assert ModelType.PRO.value == "pro"
        assert ModelType.SIMPLE.value == "simple"
        assert {m.name for m in ModelType} == {"PRO", "SIMPLE"}

    def test_source_type_type_covers_known_formats(self):
        values = {m.value for m in SourceTypeType}
        # All supported import sources.
        assert {"csv", "gdb", "kml", "tab", "gpkg", "excel",
                "layer", "shape", "geojson", "otherfile"} <= values

    def test_target_type_type_covers_known_formats(self):
        values = {m.value for m in TargetTypeType}
        # All supported export targets - fewer than sources (no gdb/kml/tab).
        assert {"csv", "gpkg", "excel", "layer", "shape", "geojson"} <= values

    def test_operation_type_has_overlay_operations(self):
        values = {m.value for m in OperationType}
        # Server enum uses PascalCase / mixedCase, not lowercase.
        assert "Clip" in values
        assert "Within" in values
        assert "Intersect" in values
        assert "Subtraction" in values
        assert "SymDifference" in values


class TestCreateTaskPrototype:
    """create_task_prototype wraps StartParameters into TaskPrototypeDto."""

    def test_returns_task_prototype_dto(self):
        sp = NetengineRouteStartParameters(x1=1, y1=2, x2=3, y2=4)
        proto = create_task_prototype(
            task_type="netEngine:route", start_parameters=sp
        )
        assert isinstance(proto, TaskPrototypeDto)
        assert proto.subTaskSettings is not None
        assert len(proto.subTaskSettings) == 1

    def test_task_type_main_type_only_in_subtask(self):
        # "mainType:subType" -> SubTaskSettingsDto.type = mainType.
        sp = NetengineRouteStartParameters()
        proto = create_task_prototype(
            task_type="netEngine:route", start_parameters=sp
        )
        sub = proto.subTaskSettings[0]
        assert isinstance(sub, SubTaskSettingsDto)
        assert sub.type == "netEngine"

    def test_task_type_without_subtype(self):
        # No ":" - whole string is mainType.
        sp = BaseStartParameters()
        proto = create_task_prototype(
            task_type="netEngine", start_parameters=sp
        )
        assert proto.subTaskSettings[0].type == "netEngine"

    def test_optional_fields_propagate(self):
        sp = BaseStartParameters()
        proto = create_task_prototype(
            task_type="x:y",
            start_parameters=sp,
            description="hello",
            enabled=True,
            order=5,
        )
        assert proto.description == "hello"
        assert proto.enabled is True
        assert proto.subTaskSettings[0].order == 5

    def test_start_parameters_attached_to_subtask(self):
        sp = NetengineRouteStartParameters(x1=1.0, y1=2.0)
        proto = create_task_prototype(
            task_type="netEngine:route", start_parameters=sp
        )
        # The SP object itself ends up inside subTaskSettings.
        assert proto.subTaskSettings[0].startParameters is sp


class TestCreateStartParameters:
    """create_start_parameters dispatches by task_type string."""

    def test_netengine_route_returns_correct_class(self):
        sp = create_start_parameters(
            "netEngine:route",
            x1=1, y1=2, x2=3, y2=4,
            srIn=4326, srOut=4326,
        )
        assert isinstance(sp, NetengineRouteStartParameters)
        assert sp.x1 == 1
        assert sp.y1 == 2
        assert sp.x2 == 3
        assert sp.y2 == 4
        # Aliases (srIn/srOut) populate python_name fields.
        assert sp.sr_in == 4326
        assert sp.sr_out == 4326

    def test_unknown_task_type_raises_value_error(self):
        with pytest.raises(ValueError, match="Unknown task type"):
            create_start_parameters("nope:nope")

    def test_unknown_task_type_message_includes_input(self):
        with pytest.raises(ValueError) as excinfo:
            create_start_parameters("foo:bar")
        assert "foo:bar" in str(excinfo.value)

    def test_importexport_importexport_not_in_main_dispatch(self):
        # The combined "importExport:importExport" path is intentionally
        # NOT registered here - it goes through create_importexport_start_parameters
        # in importexport_conditional. The main dispatch must reject it.
        with pytest.raises(ValueError, match="Unknown task type"):
            create_start_parameters("importExport:importExport")

    def test_dataschema_subtype_works(self):
        # The other importExport subtype ("dataSchema") IS in the main dispatch.
        from evergis_tools.tasks.worker_models import (
            ImportexportImportexportdataschemaStartParameters,
        )
        sp = create_start_parameters("importExport:importExport/dataSchema")
        assert isinstance(sp, ImportexportImportexportdataschemaStartParameters)


class TestProcessingTypeTypo:
    """Server contract has a typo - 'proccessingType' (double c).

    Models must preserve the typo so the wire payload matches the server.
    """

    def test_models_source_has_typo_alias(self):
        text = (_WORKER_MODELS_DIR / "models.py").read_text(encoding="utf-8")
        # Both occurrences (python_name 'proccessing_type' and alias 'proccessingType')
        # must exist.
        assert "proccessingType" in text
        assert "proccessing_type" in text

    def test_models_source_has_no_corrected_spelling(self):
        text = (_WORKER_MODELS_DIR / "models.py").read_text(encoding="utf-8")
        # Anti-test: the fix-up would silently break round-trip with the server.
        # We assert the typo is the ONLY spelling present.
        assert re.search(r"\bprocessingType\b", text) is None
        assert re.search(r"\bprocessing_type\b", text) is None

    def test_netengine_odmatrix_has_proccessing_type_field(self):
        # Confirm the field is actually on the model (alias path).
        from evergis_tools.tasks.worker_models import (
            NetengineOdmatrixStartParameters,
        )
        sp = NetengineOdmatrixStartParameters(proccessingType="foo")
        assert sp.proccessing_type == "foo"

    def test_geoprocessing_buffer_has_proccessing_type_field(self):
        from evergis_tools.tasks.worker_models import (
            GeoprocessingBufferStartParameters,
        )
        sp = GeoprocessingBufferStartParameters(proccessingType="bar")
        assert sp.proccessing_type == "bar"


class TestConditionalImportExportCount:
    """importexport_conditional must declare exactly the documented set."""

    def test_concrete_start_parameters_count(self):
        # Source file is the source of truth - count `^class *ToToStartParameters`
        # patterns to catch any drift between generator runs.
        text = (
            _WORKER_MODELS_DIR / "importexport_conditional.py"
        ).read_text(encoding="utf-8")
        concrete = re.findall(
            r"^class \w+To\w+StartParameters\(", text, flags=re.MULTILINE
        )
        assert len(concrete) == 54, (
            f"expected 54 concrete *To*StartParameters classes, got {len(concrete)}"
        )

    def test_total_start_parameters_classes_count(self):
        # 54 concrete + 1 base = 55 total `class ... StartParameters(`.
        text = (
            _WORKER_MODELS_DIR / "importexport_conditional.py"
        ).read_text(encoding="utf-8")
        all_sp = re.findall(
            r"^class \w+StartParameters\(", text, flags=re.MULTILINE
        )
        assert len(all_sp) == 55

    def test_base_importexport_inherits_base_start_parameters(self):
        assert issubclass(BaseImportexportStartParameters, BaseStartParameters)


class TestConditionalAliases:
    """Long-form ImportexportSource*Target*StartParameters aliases.

    Kept for backward compatibility - they map 1:1 to the short *To*
    classes via `is` identity (not subclassing).
    """

    def test_csv_to_layer_alias_is_identity(self):
        assert (
            ImportexportSourceCsvTargetLayerStartParameters
            is CsvToLayerStartParameters
        )

    def test_layer_to_gpkg_alias_is_identity(self):
        # Spot-check a second pair from a different source type.
        assert (
            iec.ImportexportSourceLayerTargetGpkgStartParameters
            is iec.LayerToGpkgStartParameters
        )

    def test_excel_to_geojson_alias_is_identity(self):
        assert (
            iec.ImportexportSourceExcelTargetGeojsonStartParameters
            is iec.ExcelToGeojsonStartParameters
        )

    def test_otherfile_to_layer_alias_is_identity(self):
        # otherfile is the catch-all source - check its layer target alias.
        assert (
            iec.ImportexportSourceOtherfileTargetLayerStartParameters
            is iec.OtherfileToLayerStartParameters
        )
