# -*- coding: utf-8 -*-
"""Tests for layers/_utils.py -- layer utility functions."""

import pytest
from unittest.mock import MagicMock

import geopandas as gpd
from shapely.geometry import Point

from evergis_api.schemas import (
    AttributeType,
    AttributesConfigurationDc,
    AttributeConfigurationDc,
    QueryLayerServiceEqlParameterConfigurationDc,
)

from evergis_tools.layers._utils import (
    _convert_geometry_type,
    _infer_attribute_type,
    _convert_eql_parameters,
    _normalize_layer_name,
    create_eql_attributes_configuration,
)


# =====================================================================
# _convert_geometry_type
# =====================================================================


class TestConvertGeometryType:
    """Tests for _convert_geometry_type()."""

    @pytest.mark.parametrize("input_val,expected", [
        ("Point", AttributeType.POINT),
        ("point", AttributeType.POINT),
        ("POINT", AttributeType.POINT),
        ("LineString", AttributeType.LINESTRING),
        ("linestring", AttributeType.LINESTRING),
        ("Polygon", AttributeType.POLYGON),
        ("polygon", AttributeType.POLYGON),
        ("MultiPoint", AttributeType.MULTIPOINT),
        ("MultiLineString", AttributeType.MULTILINESTRING),
        ("MultiPolygon", AttributeType.MULTIPOLYGON),
        ("multipolygon", AttributeType.MULTIPOLYGON),
    ])
    def test_string_values(self, input_val, expected):
        assert _convert_geometry_type(input_val, log=False) == expected

    def test_already_enum(self):
        result = _convert_geometry_type(AttributeType.MULTIPOLYGON, log=False)
        assert result == AttributeType.MULTIPOLYGON

    def test_invalid_string_returns_fallback(self):
        result = _convert_geometry_type("InvalidType", log=False, fallback=AttributeType.POINT)
        assert result == AttributeType.POINT

    def test_invalid_string_returns_none(self):
        result = _convert_geometry_type("InvalidType", log=False)
        assert result is None

    def test_none_returns_none(self):
        result = _convert_geometry_type(None, log=False)
        assert result is None


# =====================================================================
# _infer_attribute_type
# =====================================================================


class TestInferAttributeType:
    """Tests for _infer_attribute_type()."""

    def test_bool(self):
        assert _infer_attribute_type(True) == AttributeType.BOOLEAN

    def test_int(self):
        assert _infer_attribute_type(42) == AttributeType.INT64

    def test_float(self):
        assert _infer_attribute_type(3.14) == AttributeType.DOUBLE

    def test_string(self):
        assert _infer_attribute_type("hello") == AttributeType.STRING

    def test_list_with_ints(self):
        assert _infer_attribute_type([1, 2, 3]) == AttributeType.INT64

    def test_empty_list(self):
        assert _infer_attribute_type([]) == AttributeType.STRING

    def test_bool_before_int(self):
        # bool is subclass of int, must check bool first
        assert _infer_attribute_type(False) == AttributeType.BOOLEAN


# =====================================================================
# _convert_eql_parameters
# =====================================================================


class TestConvertEqlParameters:
    """Tests for _convert_eql_parameters()."""

    def test_none_returns_none(self):
        assert _convert_eql_parameters(None) is None

    def test_simple_string(self):
        result = _convert_eql_parameters({"@status": "active"})
        assert "@status" in result
        param = result["@status"]
        assert isinstance(param, QueryLayerServiceEqlParameterConfigurationDc)
        assert param.default == "active"
        assert param.type == AttributeType.STRING
        assert param.alias == "status"

    def test_simple_int(self):
        result = _convert_eql_parameters({"@count": 10})
        assert result["@count"].type == AttributeType.INT64
        assert result["@count"].default == 10

    def test_simple_float(self):
        result = _convert_eql_parameters({"@ratio": 3.14})
        assert result["@ratio"].type == AttributeType.DOUBLE

    def test_simple_bool(self):
        result = _convert_eql_parameters({"@active": True})
        assert result["@active"].type == AttributeType.BOOLEAN

    def test_list_value(self):
        result = _convert_eql_parameters({"@ids": [1, 2, 3]})
        assert result["@ids"].isArray is True

    def test_passthrough_config_object(self):
        config = QueryLayerServiceEqlParameterConfigurationDc(
            type=AttributeType.STRING, default="test"
        )
        result = _convert_eql_parameters({"@p": config})
        assert result["@p"] is config

    def test_dict_with_default_key(self):
        result = _convert_eql_parameters(
            {"@p": {"type": "String", "default": "val", "alias": "p"}}
        )
        assert isinstance(result["@p"], QueryLayerServiceEqlParameterConfigurationDc)

    def test_alias_strips_at(self):
        result = _convert_eql_parameters({"@my_param": "x"})
        assert result["@my_param"].alias == "my_param"

    def test_no_at_prefix(self):
        result = _convert_eql_parameters({"param": "x"})
        assert result["param"].alias == "param"


# =====================================================================
# _normalize_layer_name
# =====================================================================


class TestNormalizeLayerName:
    """Tests for _normalize_layer_name()."""

    @pytest.fixture(autouse=True)
    def setup_mock_client(self):
        self.client = MagicMock()
        self.client.account.get_user_info.return_value = MagicMock(username="testuser")

    def test_simple_name(self):
        result = _normalize_layer_name(self.client, "my_layer", log=False)
        assert result == "testuser.my_layer"

    def test_already_prefixed(self):
        result = _normalize_layer_name(self.client, "otheruser.my_layer", log=False)
        assert result == "otheruser.my_layer"

    def test_cyrillic_transliterated(self):
        result = _normalize_layer_name(self.client, "Мой Слой", log=False)
        assert result.startswith("testuser.")
        # Should be transliterated and lowercased
        table_part = result.split(".", 1)[1]
        assert table_part.isascii()
        assert table_part.islower() or "_" in table_part

    def test_preserves_provided_username(self):
        result = _normalize_layer_name(self.client, "admin.layer", log=False)
        assert result.startswith("admin.")


# =====================================================================
# create_eql_attributes_configuration
# =====================================================================


class TestCreateEqlAttributesConfiguration:
    """Tests for create_eql_attributes_configuration()."""

    def test_basic_gdf(self):
        gdf = gpd.GeoDataFrame(
            {"name": ["A", "B"], "value": [1, 2]},
            geometry=[Point(0, 0), Point(1, 1)],
            crs="EPSG:4326",
        )
        result = create_eql_attributes_configuration(
            gdf, "test_layer",
            geometry_attribute="geometry",
            geometry_type="Point",
            log=False,
        )
        assert isinstance(result, AttributesConfigurationDc)
        assert result.idAttribute == "gid"
        assert result.geometryAttribute == "geometry"

        # Check attributes list
        attr_names = {a.attributeName for a in result.attributes}
        assert "gid" in attr_names
        assert "name" in attr_names
        assert "value" in attr_names

    def test_custom_id_attribute(self):
        gdf = gpd.GeoDataFrame(
            {"my_id": [1, 2], "name": ["A", "B"]},
            geometry=[Point(0, 0), Point(1, 1)],
            crs="EPSG:4326",
        )
        result = create_eql_attributes_configuration(
            gdf, "test_layer", id_attribute="my_id", geometry_type="Point", log=False
        )
        assert result.idAttribute == "my_id"

    def test_no_geometry_type(self):
        gdf = gpd.GeoDataFrame(
            {"name": ["A"]},
            geometry=[Point(0, 0)],
            crs="EPSG:4326",
        )
        result = create_eql_attributes_configuration(
            gdf, "test_layer", geometry_type=None, log=False
        )
        assert result.geometryAttribute is None

    def test_order_attribute(self):
        gdf = gpd.GeoDataFrame(
            {"name": ["A"]},
            geometry=[Point(0, 0)],
            crs="EPSG:4326",
        )
        result = create_eql_attributes_configuration(
            gdf, "test_layer", order_attribute="name", log=False
        )
        assert result.orderAttribute == "name"

    def test_gid_is_not_editable(self):
        gdf = gpd.GeoDataFrame(
            {"name": ["A"]},
            geometry=[Point(0, 0)],
            crs="EPSG:4326",
        )
        result = create_eql_attributes_configuration(
            gdf, "test_layer", log=False
        )
        gid_attr = next(a for a in result.attributes if a.attributeName == "gid")
        assert gid_attr.isEditable is False

    def test_attributes_are_AttributeConfigurationDc(self):
        gdf = gpd.GeoDataFrame(
            {"name": ["A"]},
            geometry=[Point(0, 0)],
            crs="EPSG:4326",
        )
        result = create_eql_attributes_configuration(
            gdf, "test_layer", log=False
        )
        for attr in result.attributes:
            assert isinstance(attr, AttributeConfigurationDc)
