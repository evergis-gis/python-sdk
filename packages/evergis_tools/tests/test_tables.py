# -*- coding: utf-8 -*-
"""Tests for evergis_tools.tables - materialized views and column operations.

All tests are pure unit tests built on MagicMock - no network access.
"""

import logging
import pytest
from unittest.mock import MagicMock

from evergis_api.schemas import (
    ColumnDescriptionDc,
    CreateViewFromQueryDc,
    CreateViewFromQueryLayerDc,
    MaterializedViewConfigurationDc,
    UpdateTableDc,
)

from evergis_tools.tables import (
    add_columns,
    create_materialized_view,
    create_materialized_view_from_layer,
    modify_table_columns,
    refresh_materialized_view,
    remove_columns,
)


# =====================================================================
# Helpers
# =====================================================================


def _make_client(username: str = "testuser") -> MagicMock:
    """Build a MagicMock client with the bits the tested helpers touch."""
    client = MagicMock()
    client.account.get_user_info.return_value = MagicMock(username=username)
    return client


# =====================================================================
# add_columns
# =====================================================================


class TestAddColumns:
    """Tests for add_columns()."""

    def test_calls_update_table_with_columns_add(self):
        client = _make_client()
        sentinel = MagicMock(name="DetailedTableInfoDc")
        client.tables.update_table.return_value = sentinel

        result = add_columns(
            client,
            "testuser.my_table",
            [{"name": "population", "type": "Int32"}],
        )

        assert result is sentinel
        client.tables.update_table.assert_called_once()
        call_kwargs = client.tables.update_table.call_args.kwargs
        assert call_kwargs["name"] == "testuser.my_table"
        body = call_kwargs["body"]
        assert isinstance(body, UpdateTableDc)
        assert body.name == "testuser.my_table"
        assert body.columnsDelete is None
        assert len(body.columnsAdd) == 1
        col = body.columnsAdd[0]
        assert isinstance(col, ColumnDescriptionDc)
        assert col.name == "population"
        # use_enum_values=True -> AttributeType serialized to its string
        assert col.type == "Int32"

    def test_legacy_nullable_key_ignored_with_warning(self, caplog):
        # the API dropped isNullable; old-style dicts must not crash
        client = _make_client()
        with caplog.at_level(logging.WARNING, logger="evergis_tools.tables.columns"):
            add_columns(
                client,
                "testuser.t",
                [{"name": "c", "type": "String", "nullable": False}],
            )

        body = client.tables.update_table.call_args.kwargs["body"]
        assert body.columnsAdd[0].name == "c"
        assert any("no longer supported" in rec.message for rec in caplog.records)

    def test_multiple_columns_mapped_in_order(self):
        client = _make_client()
        cols = [
            {"name": "a", "type": "Int32"},
            {"name": "b", "type": "String"},
            {"name": "c", "type": "Double"},
        ]
        add_columns(client, "testuser.t", cols)

        body = client.tables.update_table.call_args.kwargs["body"]
        assert [c.name for c in body.columnsAdd] == ["a", "b", "c"]
        assert [c.type for c in body.columnsAdd] == ["Int32", "String", "Double"]

    def test_exception_is_reraised(self):
        client = _make_client()
        client.tables.update_table.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            add_columns(
                client,
                "testuser.t",
                [{"name": "c", "type": "String"}],
            )

    def test_error_is_logged_before_reraise(self, caplog):
        client = _make_client()
        client.tables.update_table.side_effect = RuntimeError("server error")

        with caplog.at_level(logging.ERROR, logger="evergis_tools.tables.columns"):
            with pytest.raises(RuntimeError, match="server error"):
                add_columns(client, "testuser.t", [{"name": "c", "type": "String"}])
        assert any("server error" in rec.message for rec in caplog.records)


# =====================================================================
# remove_columns
# =====================================================================


class TestRemoveColumns:
    """Tests for remove_columns()."""

    def test_calls_update_table_with_columns_delete(self):
        client = _make_client()
        sentinel = MagicMock(name="DetailedTableInfoDc")
        client.tables.update_table.return_value = sentinel

        result = remove_columns(client, "testuser.t", ["old_col", "unused"])

        assert result is sentinel
        call_kwargs = client.tables.update_table.call_args.kwargs
        assert call_kwargs["name"] == "testuser.t"
        body = call_kwargs["body"]
        assert isinstance(body, UpdateTableDc)
        assert body.name == "testuser.t"
        assert body.columnsAdd is None
        assert body.columnsDelete == ["old_col", "unused"]

    def test_single_column(self):
        client = _make_client()
        remove_columns(client, "testuser.t", ["only"])

        body = client.tables.update_table.call_args.kwargs["body"]
        assert body.columnsDelete == ["only"]

    def test_exception_is_reraised(self):
        client = _make_client()
        client.tables.update_table.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            remove_columns(client, "testuser.t", ["c"])

    def test_error_is_logged_before_reraise(self, caplog):
        client = _make_client()
        client.tables.update_table.side_effect = RuntimeError("nope")

        with caplog.at_level(logging.ERROR, logger="evergis_tools.tables.columns"):
            with pytest.raises(RuntimeError, match="nope"):
                remove_columns(client, "testuser.t", ["c"])
        assert any("nope" in rec.message for rec in caplog.records)


# =====================================================================
# modify_table_columns
# =====================================================================


class TestModifyTableColumns:
    """Tests for modify_table_columns()."""

    def test_no_ops_raises_value_error(self):
        client = _make_client()
        with pytest.raises(ValueError, match="Nothing to do"):
            modify_table_columns(client, "testuser.t")

        client.tables.update_table.assert_not_called()

    def test_no_ops_with_empty_lists(self):
        client = _make_client()
        with pytest.raises(ValueError, match="Nothing to do"):
            modify_table_columns(
                client, "testuser.t", add_columns=[], remove_columns=[]
            )
        client.tables.update_table.assert_not_called()

    def test_only_add(self):
        client = _make_client()
        sentinel = MagicMock(name="DetailedTableInfoDc")
        client.tables.update_table.return_value = sentinel

        result = modify_table_columns(
            client,
            "testuser.t",
            add_columns=[{"name": "new_field", "type": "String"}],
        )

        assert result is sentinel
        body = client.tables.update_table.call_args.kwargs["body"]
        assert isinstance(body, UpdateTableDc)
        assert body.columnsDelete is None
        assert len(body.columnsAdd) == 1
        assert body.columnsAdd[0].name == "new_field"
        assert body.columnsAdd[0].type == "String"

    def test_only_remove(self):
        client = _make_client()
        sentinel = MagicMock(name="DetailedTableInfoDc")
        client.tables.update_table.return_value = sentinel

        result = modify_table_columns(
            client, "testuser.t", remove_columns=["old_field"]
        )

        assert result is sentinel
        body = client.tables.update_table.call_args.kwargs["body"]
        assert isinstance(body, UpdateTableDc)
        assert body.columnsAdd is None
        assert body.columnsDelete == ["old_field"]

    def test_both_add_and_remove(self):
        client = _make_client()
        sentinel = MagicMock(name="DetailedTableInfoDc")
        client.tables.update_table.return_value = sentinel

        result = modify_table_columns(
            client,
            "testuser.t",
            add_columns=[{"name": "new_field", "type": "String"}],
            remove_columns=["old_field"],
        )

        assert result is sentinel
        body = client.tables.update_table.call_args.kwargs["body"]
        assert isinstance(body, UpdateTableDc)
        assert body.name == "testuser.t"
        assert len(body.columnsAdd) == 1
        assert body.columnsAdd[0].name == "new_field"
        assert body.columnsDelete == ["old_field"]

    def test_exception_is_reraised(self):
        client = _make_client()
        client.tables.update_table.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            modify_table_columns(client, "testuser.t", remove_columns=["c"])


# =====================================================================
# create_materialized_view
# =====================================================================


class TestCreateMaterializedView:
    """Tests for create_materialized_view()."""

    def test_calls_create_view_from_query_with_eql(self):
        client = _make_client()
        sentinel_result = MagicMock(name="DetailedTableInfoDc")
        client.tables.create_view_from_query.return_value = sentinel_result

        result = create_materialized_view(
            client,
            "my_view",
            "SELECT * FROM em.parcels WHERE area > 1000",
            log=False,
        )

        assert result is sentinel_result
        client.tables.create_view_from_query.assert_called_once()
        body = client.tables.create_view_from_query.call_args.kwargs["body"]
        assert isinstance(body, CreateViewFromQueryDc)
        assert body.eql == "SELECT * FROM em.parcels WHERE area > 1000"
        assert body.isMaterialized is True
        # username prefix added by _normalize_layer_name
        assert body.viewName == "testuser.my_view"

    def test_default_override_false(self):
        client = _make_client()
        create_materialized_view(client, "v", "SELECT 1", log=False)

        body = client.tables.create_view_from_query.call_args.kwargs["body"]
        # default override=False is stripped by _remove_none_values when value is falsy/None,
        # but for override=False pydantic may keep it - either way it must not be True
        assert body.override is not True

    def test_override_true_passed_through(self):
        client = _make_client()
        create_materialized_view(
            client, "v", "SELECT 1", override=True, log=False
        )

        body = client.tables.create_view_from_query.call_args.kwargs["body"]
        assert body.override is True

    def test_drop_cascade_true_passed_through(self):
        client = _make_client()
        create_materialized_view(
            client, "v", "SELECT 1", override=True, drop_cascade=True, log=False
        )

        body = client.tables.create_view_from_query.call_args.kwargs["body"]
        assert body.dropCascade is True

    def test_gid_column_options(self):
        client = _make_client()
        create_materialized_view(
            client,
            "v",
            "SELECT 1",
            gid_column_name="my_gid",
            add_gid_column=True,
            log=False,
        )

        body = client.tables.create_view_from_query.call_args.kwargs["body"]
        assert body.gidColumnName == "my_gid"
        assert body.addGidColumn is True

    def test_parameters_passed_through(self):
        client = _make_client()
        params = {"@status": "active"}
        create_materialized_view(
            client, "v", "SELECT * WHERE s = @status", parameters=params, log=False
        )

        body = client.tables.create_view_from_query.call_args.kwargs["body"]
        assert body.parameters == params

    def test_returns_result_object(self):
        client = _make_client()
        sentinel = MagicMock()
        client.tables.create_view_from_query.return_value = sentinel

        result = create_materialized_view(client, "v", "SELECT 1", log=False)
        assert result is sentinel

    def test_exception_is_reraised(self):
        client = _make_client()
        client.tables.create_view_from_query.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            create_materialized_view(client, "v", "SELECT 1", log=False)


# =====================================================================
# create_materialized_view_from_layer
# =====================================================================


class TestCreateMaterializedViewFromLayer:
    """Tests for create_materialized_view_from_layer()."""

    def test_calls_create_view_from_query_layer(self):
        client = _make_client()
        sentinel = MagicMock()
        client.tables.create_view_from_query_layer.return_value = sentinel

        result = create_materialized_view_from_layer(
            client, "my_view", "em.parcels", log=False
        )

        assert result is sentinel
        client.tables.create_view_from_query_layer.assert_called_once()
        body = client.tables.create_view_from_query_layer.call_args.kwargs["body"]
        assert isinstance(body, CreateViewFromQueryLayerDc)
        assert body.viewName == "testuser.my_view"
        # already has a namespace prefix - the helper keeps the provided owner
        assert body.layerName.endswith(".parcels")
        assert body.isMaterialized is True

    def test_conditions_passed_through(self):
        client = _make_client()
        create_materialized_view_from_layer(
            client,
            "v",
            "em.parcels",
            conditions=["area > 1000", "type = 'A'"],
            log=False,
        )

        body = client.tables.create_view_from_query_layer.call_args.kwargs["body"]
        assert body.conditions == ["area > 1000", "type = 'A'"]

    def test_parameters_passed_through(self):
        client = _make_client()
        params = {"@min_area": 500}
        create_materialized_view_from_layer(
            client, "v", "em.parcels", parameters=params, log=False
        )

        body = client.tables.create_view_from_query_layer.call_args.kwargs["body"]
        assert body.parameters == params

    def test_data_filter_id_passed_through(self):
        client = _make_client()
        create_materialized_view_from_layer(
            client, "v", "em.parcels", data_filter_id="filter-xyz", log=False
        )

        body = client.tables.create_view_from_query_layer.call_args.kwargs["body"]
        assert body.dataFilterId == "filter-xyz"

    def test_override_and_drop_cascade(self):
        client = _make_client()
        create_materialized_view_from_layer(
            client,
            "v",
            "em.parcels",
            override=True,
            drop_cascade=True,
            log=False,
        )

        body = client.tables.create_view_from_query_layer.call_args.kwargs["body"]
        assert body.override is True
        assert body.dropCascade is True

    def test_exception_is_reraised(self):
        client = _make_client()
        client.tables.create_view_from_query_layer.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            create_materialized_view_from_layer(
                client, "v", "em.parcels", log=False
            )


# =====================================================================
# refresh_materialized_view
# =====================================================================


class TestRefreshMaterializedView:
    """Tests for refresh_materialized_view()."""

    def test_reads_config_then_recreates_with_override(self):
        client = _make_client()
        # build a fake materialized-view config
        mv_config = MaterializedViewConfigurationDc(
            type="MaterializedViewConfiguration",
            eql="SELECT * FROM em.parcels",
            eqlParameters={"@status": "active"},
        )
        table_info = MagicMock()
        table_info.configuration = mv_config
        client.tables.get_table_info.return_value = table_info

        refreshed = MagicMock()
        client.tables.create_view_from_query.return_value = refreshed

        result = refresh_materialized_view(client, "my_view", log=False)

        assert result is refreshed
        client.tables.get_table_info.assert_called_once_with(name="testuser.my_view")
        client.tables.create_view_from_query.assert_called_once()
        body = client.tables.create_view_from_query.call_args.kwargs["body"]
        assert isinstance(body, CreateViewFromQueryDc)
        assert body.viewName == "testuser.my_view"
        assert body.eql == "SELECT * FROM em.parcels"
        assert body.isMaterialized is True
        assert body.override is True
        assert body.parameters == {"@status": "active"}

    def test_raises_value_error_when_not_materialized_view(self):
        client = _make_client()
        # any non-MaterializedViewConfigurationDc should be rejected
        not_a_view = MagicMock(spec=[])  # no isinstance match
        table_info = MagicMock()
        table_info.configuration = not_a_view
        client.tables.get_table_info.return_value = table_info

        with pytest.raises(ValueError, match="not a materialized view"):
            refresh_materialized_view(client, "my_view", log=False)

        client.tables.create_view_from_query.assert_not_called()

    def test_create_exception_is_reraised(self):
        client = _make_client()
        mv_config = MaterializedViewConfigurationDc(
            type="MaterializedViewConfiguration",
            eql="SELECT 1",
        )
        table_info = MagicMock()
        table_info.configuration = mv_config
        client.tables.get_table_info.return_value = table_info
        client.tables.create_view_from_query.side_effect = RuntimeError("boom")

        with pytest.raises(RuntimeError, match="boom"):
            refresh_materialized_view(client, "my_view", log=False)
