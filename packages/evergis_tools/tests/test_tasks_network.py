# -*- coding: utf-8 -*-
"""Tests for evergis_tools.tasks.network - isochrones and OD-matrix helpers.

Unit-only: every test patches the network boundary (``run_task``) and
intercepts the task type / start_parameters that build_isochrones and
build_od_matrix would otherwise hand off to the server.
"""

from unittest.mock import MagicMock, patch

import pytest


# =====================================================================
# Imports
# =====================================================================


class TestNetworkImports:
    """Public surface of evergis_tools.tasks.network."""

    def test_build_isochrones_importable(self):
        from evergis_tools.tasks.network import build_isochrones
        assert callable(build_isochrones)

    def test_build_od_matrix_importable(self):
        from evergis_tools.tasks.network import build_od_matrix
        assert callable(build_od_matrix)

    def test_all_exports(self):
        from evergis_tools.tasks import network
        assert set(network.__all__) == {"build_isochrones", "build_od_matrix"}


# =====================================================================
# Capture helpers
# =====================================================================


def _capture_isochrones(**kwargs):
    """Run build_isochrones with the task pipeline patched.

    Wraps the real pydantic start-parameters model so we can inspect both
    the python attributes (incl. fields that resolve to None and would be
    stripped by ``model_dump(exclude_none=True)``) and the alias-form
    dict the helper actually hands to ``create_task_prototype``.

    Returns dict with: ``task_type``, ``start_parameters`` (model),
    ``start_parameters_dict`` (alias-form dict, exclude_none), and
    ``prototype_kwargs``.
    """
    from evergis_tools.tasks.network import isochrones as iso_mod
    from evergis_tools.tasks.worker_models import NetengineAvailabilityareaStartParameters

    captured = {}

    def wrapped_start_params(**sp_kwargs):
        sp = NetengineAvailabilityareaStartParameters(**sp_kwargs)
        captured["start_parameters"] = sp
        return sp

    def fake_create(task_type, start_parameters, **proto_kwargs):
        captured["task_type"] = task_type
        captured["start_parameters_dict"] = start_parameters
        captured["prototype_kwargs"] = proto_kwargs
        return MagicMock(name="TaskPrototypeDto")

    with patch.object(iso_mod, "NetengineAvailabilityareaStartParameters", side_effect=wrapped_start_params), \
         patch.object(iso_mod, "create_task_prototype", side_effect=fake_create) as cp, \
         patch.object(iso_mod, "run_task", return_value=MagicMock(name="TaskExecutionResult")) as rt:
        result = iso_mod.build_isochrones(client=MagicMock(), **kwargs)

    captured["result"] = result
    captured["create_called"] = cp.called
    captured["run_called"] = rt.called
    return captured


def _capture_od_matrix(**kwargs):
    """Run build_od_matrix with the task pipeline patched (see _capture_isochrones)."""
    from evergis_tools.tasks.network import odmatrix as od_mod
    from evergis_tools.tasks.worker_models import NetengineOdmatrixStartParameters

    captured = {}

    def wrapped_start_params(**sp_kwargs):
        sp = NetengineOdmatrixStartParameters(**sp_kwargs)
        captured["start_parameters"] = sp
        return sp

    def fake_create(task_type, start_parameters, **proto_kwargs):
        captured["task_type"] = task_type
        captured["start_parameters_dict"] = start_parameters
        captured["prototype_kwargs"] = proto_kwargs
        return MagicMock(name="TaskPrototypeDto")

    with patch.object(od_mod, "NetengineOdmatrixStartParameters", side_effect=wrapped_start_params), \
         patch.object(od_mod, "create_task_prototype", side_effect=fake_create) as cp, \
         patch.object(od_mod, "run_task", return_value=MagicMock(name="TaskExecutionResult")) as rt:
        result = od_mod.build_od_matrix(client=MagicMock(), **kwargs)

    captured["result"] = result
    captured["create_called"] = cp.called
    captured["run_called"] = rt.called
    return captured


# =====================================================================
# build_isochrones
# =====================================================================


class TestBuildIsochrones:
    """Unit tests for build_isochrones - inspects the constructed task."""

    def test_task_type_is_netengine_availability_area(self):
        cap = _capture_isochrones(source_layer_name="src")
        assert cap["task_type"] == "netEngine:availabilityArea"

    def test_proccessing_type_has_double_c(self):
        # Server-side parameter name has a typo ("proccessingType" with double-c)
        # that the API still requires - we must not silently fix it.
        cap = _capture_isochrones(source_layer_name="src")
        sp = cap["start_parameters"]
        assert sp.proccessing_type == "availabilityArea"
        dumped = cap["start_parameters_dict"]  # alias-form dict, exclude_none
        assert "proccessingType" in dumped
        assert dumped["proccessingType"] == "availabilityArea"
        assert "processingType" not in dumped  # single-c must not appear

    def test_default_provider_is_sproute_isochrone_pedestrian(self):
        from evergis_tools.tasks.worker_models import ProvidernameType

        cap = _capture_isochrones(source_layer_name="src")
        sp = cap["start_parameters"]
        assert sp.provider_name == ProvidernameType.SPROUTE_ISOCHRONE_PEDESTRIAN
        assert sp.provider_name.value == "sproute_isochrone_pedestrian"

    def test_provider_accepts_string(self):
        from evergis_tools.tasks.worker_models import ProvidernameType

        cap = _capture_isochrones(
            source_layer_name="src",
            provider_name="osrm_car",
        )
        assert cap["start_parameters"].provider_name == ProvidernameType.OSRM_CAR

    def test_provider_accepts_enum(self):
        from evergis_tools.tasks.worker_models import ProvidernameType

        cap = _capture_isochrones(
            source_layer_name="src",
            provider_name=ProvidernameType.TWOGIS_WALK,
        )
        assert cap["start_parameters"].provider_name == ProvidernameType.TWOGIS_WALK

    def test_default_source_id_and_geometry_attributes(self):
        cap = _capture_isochrones(source_layer_name="src")
        sl = cap["start_parameters"].source_layer
        assert sl.id_attribute == "gid"
        assert sl.geometry_attribute == "geometry"

    def test_output_attribute_defaults_are_none(self):
        # Isochrones output attribute names default to None - the server
        # picks its own defaults. The wrapper exposes the knobs but does
        # NOT bake in opinionated defaults the way build_od_matrix does.
        cap = _capture_isochrones(source_layer_name="src")
        sp = cap["start_parameters"]
        assert sp.id_attribute_name is None
        assert sp.geometry_attribute_name is None
        assert sp.duration_attribute_name is None
        assert sp.base_object_id_attribute_name is None
        assert sp.route_center_x_attribute_name is None
        assert sp.route_center_y_attribute_name is None

    def test_default_constants_match_module(self):
        from evergis_tools.tasks.network import isochrones as iso_mod
        from evergis_tools.tasks.worker_models import ProvidernameType

        assert iso_mod.DEFAULT_SOURCE_ID_ATTRIBUTE == "gid"
        assert iso_mod.DEFAULT_SOURCE_GEOMETRY_ATTRIBUTE == "geometry"
        assert iso_mod.DEFAULT_PROVIDER == ProvidernameType.SPROUTE_ISOCHRONE_PEDESTRIAN

    def test_start_if_previous_not_finished_default_false(self):
        cap = _capture_isochrones(source_layer_name="src")
        assert cap["prototype_kwargs"]["start_if_previous_not_finished"] is False

    def test_start_if_previous_error_default_true(self):
        cap = _capture_isochrones(source_layer_name="src")
        assert cap["prototype_kwargs"]["start_if_previous_error"] is True

    def test_enabled_default_true(self):
        cap = _capture_isochrones(source_layer_name="src")
        assert cap["prototype_kwargs"]["enabled"] is True

    def test_requires_eql_or_layer_name(self):
        from evergis_tools.tasks.network import build_isochrones

        with pytest.raises(ValueError, match="source_layer_eql.*source_layer_name"):
            build_isochrones(client=MagicMock())

    def test_eql_is_passed_through(self):
        cap = _capture_isochrones(source_layer_eql="SELECT * FROM x")
        sl = cap["start_parameters"].source_layer
        assert sl.eql == "SELECT * FROM x"
        assert sl.layer_name is None

    def test_layer_name_is_passed_through(self):
        cap = _capture_isochrones(source_layer_name="schema.table")
        sl = cap["start_parameters"].source_layer
        assert sl.layer_name == "schema.table"
        assert sl.eql is None

    def test_target_layer_omitted_when_not_provided(self):
        cap = _capture_isochrones(source_layer_name="src")
        assert cap["start_parameters"].target_layer is None

    def test_target_layer_built_when_provided(self):
        cap = _capture_isochrones(
            source_layer_name="src",
            target_layer="user.evg_iso_out",
            target_layer_alias="iso output",
        )
        tl = cap["start_parameters"].target_layer
        assert tl is not None
        assert tl.name == "user.evg_iso_out"
        assert tl.alias == "iso output"

    def test_custom_output_attribute_names_forwarded(self):
        cap = _capture_isochrones(
            source_layer_name="src",
            id_attribute_name="my_id",
            geometry_attribute_name="my_geom",
            duration_attribute_name="dur_s",
            base_object_id_attribute_name="base_gid",
            route_center_x_attribute_name="cx",
            route_center_y_attribute_name="cy",
        )
        sp = cap["start_parameters"]
        assert sp.id_attribute_name == "my_id"
        assert sp.geometry_attribute_name == "my_geom"
        assert sp.duration_attribute_name == "dur_s"
        assert sp.base_object_id_attribute_name == "base_gid"
        assert sp.route_center_x_attribute_name == "cx"
        assert sp.route_center_y_attribute_name == "cy"

    def test_defer_returns_taskstep_without_calling_run(self):
        from evergis_tools.tasks.network import isochrones as iso_mod
        from evergis_tools.tasks.pipeline import TaskStep

        with patch.object(iso_mod, "run_task") as rt, \
             patch.object(iso_mod, "create_task_prototype") as cp:
            step = iso_mod.build_isochrones(
                client=MagicMock(),
                source_layer_name="src",
                defer=True,
            )
        assert isinstance(step, TaskStep)
        assert step.task_type == "netEngine"
        assert step.start_parameters["proccessingType"] == "availabilityArea"
        assert rt.called is False
        assert cp.called is False


# =====================================================================
# build_od_matrix
# =====================================================================


class TestBuildOdMatrix:
    """Unit tests for build_od_matrix - inspects the constructed task."""

    def _ok_kwargs(self, **overrides):
        base = {
            "target_layer": "user.evg_od_out",
            "source_from_layer_name": "from_src",
            "source_to_layer_name": "to_src",
        }
        base.update(overrides)
        return base

    def test_task_type_is_netengine_odmatrix(self):
        cap = _capture_od_matrix(**self._ok_kwargs())
        assert cap["task_type"] == "netEngine:ODMatrix"

    def test_proccessing_type_has_double_c(self):
        # Server requires "proccessingType" (double-c). Same quirk as
        # availabilityArea - do not "fix" it.
        cap = _capture_od_matrix(**self._ok_kwargs())
        sp = cap["start_parameters"]
        assert sp.proccessing_type == "ODMatrix"
        dumped = cap["start_parameters_dict"]
        assert dumped["proccessingType"] == "ODMatrix"
        assert "processingType" not in dumped  # single-c must not appear

    def test_default_output_column_names(self):
        # Defaults: gid / from / to / transport_type / weight_parameter / distance.
        cap = _capture_od_matrix(**self._ok_kwargs())
        sp = cap["start_parameters"]
        assert sp.id_attribute_name == "gid"
        assert sp.id_from_attribute_name == "from"
        assert sp.id_to_attribute_name == "to"
        assert sp.transport_type_attribute_name == "transport_type"
        assert sp.weight_parameter_attribute_name == "weight_parameter"
        assert sp.distance_attribute_name == "distance"

    def test_default_constants_match_module(self):
        from evergis_tools.tasks.network import odmatrix as od_mod

        assert od_mod.DEFAULT_SOURCE_ID_ATTRIBUTE == "gid"
        assert od_mod.DEFAULT_SOURCE_GEOMETRY_ATTRIBUTE == "geometry"
        assert od_mod.DEFAULT_ID_ATTRIBUTE_NAME == "gid"
        assert od_mod.DEFAULT_ID_FROM_ATTRIBUTE_NAME == "from"
        assert od_mod.DEFAULT_ID_TO_ATTRIBUTE_NAME == "to"
        assert od_mod.DEFAULT_TRANSPORT_TYPE_ATTRIBUTE_NAME == "transport_type"
        assert od_mod.DEFAULT_WEIGHT_PARAMETER_ATTRIBUTE_NAME == "weight_parameter"
        assert od_mod.DEFAULT_DISTANCE_ATTRIBUTE_NAME == "distance"

    def test_start_if_previous_not_finished_default_true(self):
        # Differs from build_isochrones, which defaults to False.
        cap = _capture_od_matrix(**self._ok_kwargs())
        assert cap["prototype_kwargs"]["start_if_previous_not_finished"] is True

    def test_start_if_previous_error_default_true(self):
        cap = _capture_od_matrix(**self._ok_kwargs())
        assert cap["prototype_kwargs"]["start_if_previous_error"] is True

    def test_enabled_default_true(self):
        cap = _capture_od_matrix(**self._ok_kwargs())
        assert cap["prototype_kwargs"]["enabled"] is True

    def test_requires_target_layer(self):
        from evergis_tools.tasks.network import build_od_matrix

        with pytest.raises(ValueError, match="target_layer"):
            build_od_matrix(
                client=MagicMock(),
                target_layer="",
                source_from_layer_name="a",
                source_to_layer_name="b",
            )

    def test_requires_from_source(self):
        from evergis_tools.tasks.network import build_od_matrix

        with pytest.raises(ValueError, match="source_from_layer_eql.*source_from_layer_name"):
            build_od_matrix(
                client=MagicMock(),
                target_layer="user.evg_od_out",
                source_to_layer_name="to_src",
            )

    def test_requires_to_source(self):
        from evergis_tools.tasks.network import build_od_matrix

        with pytest.raises(ValueError, match="source_to_layer_eql.*source_to_layer_name"):
            build_od_matrix(
                client=MagicMock(),
                target_layer="user.evg_od_out",
                source_from_layer_name="from_src",
            )

    def test_default_source_attributes(self):
        cap = _capture_od_matrix(**self._ok_kwargs())
        sp = cap["start_parameters"]
        assert sp.source_from_layer.id_attribute == "gid"
        assert sp.source_from_layer.geometry_attribute == "geometry"
        assert sp.source_to_layer.id_attribute == "gid"
        assert sp.source_to_layer.geometry_attribute == "geometry"

    def test_target_layer_built(self):
        cap = _capture_od_matrix(**self._ok_kwargs(
            target_layer_alias="od output",
        ))
        tl = cap["start_parameters"].target_layer
        assert tl.name == "user.evg_od_out"
        assert tl.alias == "od output"

    def test_transport_type_forwarded(self):
        cap = _capture_od_matrix(**self._ok_kwargs(transport_type="car"))
        assert cap["start_parameters"].transport_type == "car"

    def test_transport_type_default_none(self):
        cap = _capture_od_matrix(**self._ok_kwargs())
        assert cap["start_parameters"].transport_type is None

    def test_attribute_type_mapping_forwarded(self):
        mapping = {"distance": "Double", "weight_parameter": "Double"}
        cap = _capture_od_matrix(**self._ok_kwargs(attribute_type_mapping=mapping))
        assert cap["start_parameters"].attribute_type_mapping == mapping

    def test_default_values_forwarded(self):
        defaults = {"transport_type": "car", "weight_parameter": 0.0}
        cap = _capture_od_matrix(**self._ok_kwargs(default_values=defaults))
        assert cap["start_parameters"].default_values == defaults

    def test_eql_sources_passed_through(self):
        cap = _capture_od_matrix(
            target_layer="user.evg_od_out",
            source_from_layer_eql="SELECT * FROM a",
            source_to_layer_eql="SELECT * FROM b",
        )
        sp = cap["start_parameters"]
        assert sp.source_from_layer.eql == "SELECT * FROM a"
        assert sp.source_from_layer.layer_name is None
        assert sp.source_to_layer.eql == "SELECT * FROM b"
        assert sp.source_to_layer.layer_name is None

    def test_source_conditions_passed_through(self):
        cap = _capture_od_matrix(**self._ok_kwargs(
            source_from_condition="kind = 'origin'",
            source_to_condition="kind = 'dest'",
        ))
        sp = cap["start_parameters"]
        assert sp.source_from_layer.condition == "kind = 'origin'"
        assert sp.source_to_layer.condition == "kind = 'dest'"

    def test_custom_output_column_names_forwarded(self):
        cap = _capture_od_matrix(**self._ok_kwargs(
            id_attribute_name="row_id",
            id_from_attribute_name="src_id",
            id_to_attribute_name="dst_id",
            transport_type_attribute_name="mode",
            weight_parameter_attribute_name="weight",
            distance_attribute_name="dist_m",
        ))
        sp = cap["start_parameters"]
        assert sp.id_attribute_name == "row_id"
        assert sp.id_from_attribute_name == "src_id"
        assert sp.id_to_attribute_name == "dst_id"
        assert sp.transport_type_attribute_name == "mode"
        assert sp.weight_parameter_attribute_name == "weight"
        assert sp.distance_attribute_name == "dist_m"

    def test_defer_returns_taskstep_without_calling_run(self):
        from evergis_tools.tasks.network import odmatrix as od_mod
        from evergis_tools.tasks.pipeline import TaskStep

        with patch.object(od_mod, "run_task") as rt, \
             patch.object(od_mod, "create_task_prototype") as cp:
            step = od_mod.build_od_matrix(
                client=MagicMock(),
                target_layer="user.evg_od_out",
                source_from_layer_name="from_src",
                source_to_layer_name="to_src",
                defer=True,
            )
        assert isinstance(step, TaskStep)
        assert step.task_type == "netEngine"
        assert step.start_parameters["proccessingType"] == "ODMatrix"
        assert rt.called is False
        assert cp.called is False
