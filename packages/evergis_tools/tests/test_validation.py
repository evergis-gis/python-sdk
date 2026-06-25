# -*- coding: utf-8 -*-
"""Tests for validation.py -- generic data validation helpers."""

import pytest

from evergis_tools.validation import (
    validate_feature_properties,
    validate_pagination_params,
)


class TestValidateFeatureProperties:
    """Tests for validate_feature_properties()."""

    def test_empty_dict_no_required(self):
        # No required fields -> any dict (incl. empty) is valid.
        assert validate_feature_properties({}) is True

    def test_basic_dict_no_required(self):
        assert validate_feature_properties({"id": 1, "name": "x"}) is True

    def test_all_required_present(self):
        props = {"id": 1, "name": "Feature1"}
        assert validate_feature_properties(props, ["id", "name"]) is True

    def test_required_subset_present(self):
        props = {"id": 1, "name": "Feature1", "extra": "y"}
        assert validate_feature_properties(props, ["id"]) is True

    def test_missing_required_field(self):
        props = {"id": 1, "name": "Feature1"}
        assert validate_feature_properties(props, ["id", "missing"]) is False

    def test_required_field_none(self):
        # None value on a required field is treated as missing.
        props = {"id": None, "name": "Feature1"}
        assert validate_feature_properties(props, ["id"]) is False

    def test_required_field_empty_string(self):
        assert validate_feature_properties({"name": ""}, ["name"]) is False

    def test_required_field_whitespace_only(self):
        # Whitespace-only strings are stripped to empty -> treated as missing.
        assert validate_feature_properties({"name": "   "}, ["name"]) is False

    def test_required_field_zero_is_valid(self):
        # 0 is a legitimate value, must not be treated as null-like.
        assert validate_feature_properties({"count": 0}, ["count"]) is True

    def test_required_field_false_is_valid(self):
        assert validate_feature_properties({"flag": False}, ["flag"]) is True

    def test_empty_required_list(self):
        assert validate_feature_properties({"id": 1}, []) is True

    def test_required_none_default(self):
        # Default required_fields=None means no required check.
        assert validate_feature_properties({"id": 1}, None) is True

    @pytest.mark.parametrize("bad_input", [
        None,
        "not a dict",
        [1, 2, 3],
        42,
        3.14,
        True,
    ])
    def test_non_dict_input_returns_false(self, bad_input):
        assert validate_feature_properties(bad_input) is False

    def test_unicode_values_valid(self):
        props = {"name": "Москва"}
        assert validate_feature_properties(props, ["name"]) is True


class TestValidatePaginationParams:
    """Tests for validate_pagination_params()."""

    def test_no_args(self):
        # Both None -> nothing to validate, valid by default.
        assert validate_pagination_params() is True

    def test_both_none_explicit(self):
        assert validate_pagination_params(None, None) is True

    def test_valid_page_and_limit(self):
        assert validate_pagination_params(1, 100) is True

    def test_only_page_valid(self):
        assert validate_pagination_params(page=5) is True

    def test_only_limit_valid(self):
        assert validate_pagination_params(limit=50) is True

    @pytest.mark.parametrize("page", [1, 2, 100, 999999])
    def test_valid_page_values(self, page):
        assert validate_pagination_params(page=page) is True

    @pytest.mark.parametrize("page", [0, -1, -100])
    def test_page_below_one_invalid(self, page):
        assert validate_pagination_params(page=page) is False

    @pytest.mark.parametrize("limit", [1, 100, 1000, 10000])
    def test_valid_limit_values(self, limit):
        assert validate_pagination_params(limit=limit) is True

    @pytest.mark.parametrize("limit", [0, -1, -100])
    def test_limit_below_one_invalid(self, limit):
        assert validate_pagination_params(limit=limit) is False

    @pytest.mark.parametrize("limit", [10001, 20000, 100000])
    def test_limit_above_max_invalid(self, limit):
        # Server cap at 10000 - bigger limits are rejected client-side.
        assert validate_pagination_params(limit=limit) is False

    def test_limit_at_boundary_10000(self):
        # 10000 inclusive upper bound.
        assert validate_pagination_params(limit=10000) is True

    def test_page_at_boundary_1(self):
        assert validate_pagination_params(page=1) is True

    @pytest.mark.parametrize("page", [1.5, "1", [1], {"page": 1}])
    def test_non_int_page_invalid(self, page):
        assert validate_pagination_params(page=page) is False

    @pytest.mark.parametrize("limit", [1.5, "100", [100]])
    def test_non_int_limit_invalid(self, limit):
        assert validate_pagination_params(limit=limit) is False

    def test_bool_page_accepted(self):
        # bool is a subclass of int in Python - documents current behaviour.
        # True == 1, which passes page >= 1.
        assert validate_pagination_params(page=True) is True

    def test_bool_false_page_invalid(self):
        # False == 0, fails page >= 1.
        assert validate_pagination_params(page=False) is False

    def test_invalid_page_valid_limit(self):
        # If any one of the two is invalid, the whole call is invalid.
        assert validate_pagination_params(page=0, limit=100) is False

    def test_valid_page_invalid_limit(self):
        assert validate_pagination_params(page=1, limit=99999) is False
