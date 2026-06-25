# -*- coding: utf-8 -*-
"""Tests for attributes.py -- attribute cleaning and type conversion."""

import pytest
from datetime import datetime, date
from typing import Optional, List, Dict

from evergis_api.schemas import AttributeType

from evergis_tools.attributes import (
    clean_attributes_for_evergis,
    pydantic_to_attribute_type,
    _detect_field_type,
    _is_null_like,
    _types_compatible,
)


class TestCleanAttributesForEvergis:
    """Tests for clean_attributes_for_evergis()."""

    def test_basic_types_unchanged(self):
        attrs = {"name": "Test", "count": 42, "ratio": 3.14, "active": True}
        result = clean_attributes_for_evergis(attrs)
        assert result == attrs

    def test_none_stays_none(self):
        assert clean_attributes_for_evergis({"v": None})["v"] is None

    def test_nan_becomes_none(self):
        assert clean_attributes_for_evergis({"v": float("nan")})["v"] is None

    def test_list_passes_through(self):
        # Collections must reach the server as native JSON, not stringified.
        result = clean_attributes_for_evergis({"tags": ["a", "b"]})
        assert result["tags"] == ["a", "b"]

    def test_dict_passes_through(self):
        result = clean_attributes_for_evergis({"meta": {"key": "val"}})
        assert result["meta"] == {"key": "val"}

    def test_empty_list_becomes_none(self):
        assert clean_attributes_for_evergis({"tags": []})["tags"] is None

    def test_empty_dict_becomes_none(self):
        assert clean_attributes_for_evergis({"meta": {}})["meta"] is None

    @pytest.mark.parametrize("val", ["nan", "null", "none", ""])
    def test_null_string_values(self, val):
        assert clean_attributes_for_evergis({"x": val})["x"] is None

    def test_boolean_preserved(self):
        result = clean_attributes_for_evergis({"flag": True, "other": False})
        assert result["flag"] is True
        assert result["other"] is False

    def test_tuple_normalised_to_list(self):
        # JSON has no tuple type - tuples go on the wire as JSON arrays.
        result = clean_attributes_for_evergis({"coords": (1, 2, 3)})
        assert result["coords"] == [1, 2, 3]

    def test_unicode_preserved(self):
        result = clean_attributes_for_evergis({"name": "Москва"})
        assert result["name"] == "Москва"


class TestPydanticToAttributeType:
    """Tests for pydantic_to_attribute_type()."""

    @pytest.mark.parametrize("python_type,expected", [
        (int, AttributeType.INT32),
        (str, AttributeType.STRING),
        (float, AttributeType.DOUBLE),
        (bool, AttributeType.BOOLEAN),
        (datetime, AttributeType.DATETIME),
        (date, AttributeType.DATETIME),
        (list, AttributeType.JSON),
        (dict, AttributeType.JSON),
    ])
    def test_direct_mapping(self, python_type, expected):
        assert pydantic_to_attribute_type(python_type) == expected

    def test_optional_str(self):
        assert pydantic_to_attribute_type(Optional[str]) == AttributeType.STRING

    def test_optional_int(self):
        assert pydantic_to_attribute_type(Optional[int]) == AttributeType.INT32

    def test_list_annotation(self):
        assert pydantic_to_attribute_type(List[str]) == AttributeType.JSON

    def test_dict_annotation(self):
        assert pydantic_to_attribute_type(Dict[str, int]) == AttributeType.JSON

    def test_none_type(self):
        assert pydantic_to_attribute_type(type(None)) == AttributeType.STRING

    def test_unknown_type_defaults_to_string(self):
        class Custom:
            pass
        assert pydantic_to_attribute_type(Custom) == AttributeType.STRING


class TestDetectFieldType:
    """Tests for _detect_field_type()."""

    @pytest.mark.parametrize("value,expected", [
        ("123", "Int32"),
        ("-45", "Int32"),
        ("3.14", "Double"),
        ("3,14", "Double"),
        ("2024-01-01", "DateType"),
        ("2024-01-01 12:30:00", "DateType"),
        ("2024-01-01T12:30:00Z", "DateType"),
        ('{"key": "value"}', "Json"),
        ('[1, 2, 3]', "Json"),
        ("hello", "String"),
        ("", "String"),
        ("  ", "String"),
    ])
    def test_detection(self, value, expected):
        assert _detect_field_type(value) == expected


class TestIsNullLike:
    """Tests for _is_null_like()."""

    def test_none(self):
        assert _is_null_like(None) is True

    def test_nan_float(self):
        assert _is_null_like(float("nan")) is True

    @pytest.mark.parametrize("val", ["nan", "null", "none", ""])
    def test_null_strings(self, val):
        assert _is_null_like(val) is True

    def test_normal_string(self):
        assert _is_null_like("hello") is False

    def test_zero(self):
        assert _is_null_like(0) is False

    def test_false(self):
        assert _is_null_like(False) is False


class TestTypesCompatible:
    """Tests for _types_compatible()."""

    def test_exact_match(self):
        assert _types_compatible(AttributeType.STRING, AttributeType.STRING) is True

    def test_numeric_compatible(self):
        assert _types_compatible(AttributeType.INT32, AttributeType.DOUBLE) is True
        assert _types_compatible(AttributeType.INT64, AttributeType.INT32) is True

    def test_string_json_compatible(self):
        assert _types_compatible(AttributeType.STRING, AttributeType.JSON) is True

    def test_incompatible(self):
        assert _types_compatible(AttributeType.STRING, AttributeType.INT32) is False
        assert _types_compatible(AttributeType.BOOLEAN, AttributeType.DOUBLE) is False
