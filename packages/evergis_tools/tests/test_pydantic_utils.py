# -*- coding: utf-8 -*-
"""Tests for evergis_tools.pydantic_utils: model<->layer field mapping helpers."""

from __future__ import annotations

from typing import Optional

import pytest
from pydantic import BaseModel, Field

from evergis_tools.pydantic_utils import (
    create_attribute_mappings,
    create_mappings_from_json,
    create_mappings_from_json_auto,
    create_mappings_from_pydantic,
    get_matching_fields,
    get_model_by_name,
    get_model_field_info,
    validate_layer_against_model,
)


# =====================================================================
# Test fixtures: small Pydantic models
# =====================================================================


class CityModel(BaseModel):
    city_id: str = Field(alias="CityId")
    population: Optional[int] = Field(None, alias="Population")
    name: str  # no alias


class HouseModel(BaseModel):
    house_id: str = Field(alias="HouseId")
    floors: int = 1
    area: Optional[float] = None


# =====================================================================
# get_model_field_info
# =====================================================================


class TestGetModelFieldInfo:
    """get_model_field_info()."""

    def test_returns_aliases_as_keys(self):
        info = get_model_field_info(CityModel)
        assert "CityId" in info
        assert "Population" in info
        assert "name" in info  # alias falls back to field name

    def test_python_name_stored(self):
        info = get_model_field_info(CityModel)
        assert info["CityId"]["python_name"] == "city_id"
        assert info["Population"]["python_name"] == "population"
        assert info["name"]["python_name"] == "name"

    def test_is_optional_flag(self):
        info = get_model_field_info(CityModel)
        assert info["CityId"]["is_optional"] is False
        assert info["Population"]["is_optional"] is True

    def test_type_string(self):
        info = get_model_field_info(CityModel)
        # types stored as strings (annotation name or origin name)
        assert "str" in info["CityId"]["type"] or info["CityId"]["type"] == "str"

    def test_field_reference_preserved(self):
        info = get_model_field_info(CityModel)
        # 'field' contains the FieldInfo (Pydantic v2 object)
        assert info["CityId"]["field"] is not None


# =====================================================================
# validate_layer_against_model
# =====================================================================


class TestValidateLayerAgainstModel:
    """validate_layer_against_model()."""

    def test_all_matching(self):
        layer = {
            "attributes": {
                "CityId": {"type": "String"},
                "Population": {"type": "Int32"},
                "name": {"type": "String"},
            }
        }
        report = validate_layer_against_model(layer, CityModel)
        assert report["field_count"]["matched"] == 3
        assert report["field_count"]["missing_in_model"] == 0
        assert report["field_count"]["missing_in_json"] == 0

    def test_missing_in_model(self):
        layer = {
            "attributes": {
                "CityId": {"type": "String"},
                "Population": {"type": "Int32"},
                "name": {"type": "String"},
                "Extra": {"type": "String"},
            }
        }
        report = validate_layer_against_model(layer, CityModel)
        assert "Extra" in report["missing_in_model"]
        assert report["field_count"]["missing_in_model"] == 1

    def test_missing_in_json(self):
        layer = {"attributes": {"CityId": {"type": "String"}}}
        report = validate_layer_against_model(layer, CityModel)
        assert "Population" in report["missing_in_json"]
        assert "name" in report["missing_in_json"]

    def test_geometry_attribute_skipped(self):
        layer = {
            "attributes": {
                "CityId": {"type": "String"},
                "geometry": {"type": "Polygon"},
            },
            "geometryAttribute": "geometry",
        }
        report = validate_layer_against_model(layer, CityModel)
        # geometry is excluded from matched / missing counts on JSON side
        assert "geometry" not in report["matched_fields"]
        assert "geometry" not in report["missing_in_model"]


# =====================================================================
# create_attribute_mappings
# =====================================================================


class TestCreateAttributeMappings:
    """create_attribute_mappings()."""

    def test_basic_mapping(self):
        layer = {
            "attributes": {
                "CityId": {"type": "String"},
                "Population": {"type": "String"},  # CSV-style: everything String
                "name": {"type": "String"},
            }
        }
        type_map, name_map = create_attribute_mappings(layer, CityModel)
        # Types come from the model, not from the JSON
        assert type_map["city_id"] == "String"
        assert type_map["population"] == "Int32"
        assert type_map["name"] == "String"
        # Name map: JSON-alias -> python field name
        assert name_map["CityId"] == "city_id"
        assert name_map["Population"] == "population"
        assert name_map["name"] == "name"

    def test_field_only_in_json_excluded(self):
        layer = {
            "attributes": {
                "CityId": {"type": "String"},
                "Unknown": {"type": "String"},
            }
        }
        type_map, name_map = create_attribute_mappings(layer, CityModel)
        assert "Unknown" not in name_map
        # The python side does not get an 'unknown' entry either
        assert "unknown" not in type_map

    def test_geometry_included(self):
        layer = {
            "attributes": {
                "CityId": {"type": "String"},
                "geometry": {"type": "Polygon"},
            },
            "geometryAttribute": "geometry",
        }
        type_map, name_map = create_attribute_mappings(
            layer, CityModel, exclude_geometry=False
        )
        assert type_map["geometry"] == "Polygon"
        assert name_map["geometry"] == "geometry"

    def test_geometry_excluded(self):
        layer = {
            "attributes": {
                "CityId": {"type": "String"},
                "geometry": {"type": "Polygon"},
            },
            "geometryAttribute": "geometry",
        }
        type_map, name_map = create_attribute_mappings(
            layer, CityModel, exclude_geometry=True
        )
        assert "geometry" not in type_map
        assert "geometry" not in name_map


# =====================================================================
# get_matching_fields
# =====================================================================


class TestGetMatchingFields:
    """get_matching_fields()."""

    def test_returns_alias_names(self):
        layer = {
            "attributes": {
                "CityId": {"type": "String"},
                "Population": {"type": "Int32"},
                "Unknown": {"type": "String"},
            }
        }
        result = get_matching_fields(layer, CityModel)
        assert set(result) == {"CityId", "Population"}

    def test_geometry_included_by_default(self):
        layer = {
            "attributes": {
                "CityId": {"type": "String"},
                "geometry": {"type": "Polygon"},
            },
            "geometryAttribute": "geometry",
        }
        result = get_matching_fields(layer, CityModel)
        assert "geometry" in result

    def test_geometry_excluded(self):
        layer = {
            "attributes": {
                "CityId": {"type": "String"},
                "geometry": {"type": "Polygon"},
            },
            "geometryAttribute": "geometry",
        }
        result = get_matching_fields(layer, CityModel, exclude_geometry=True)
        assert "geometry" not in result


# =====================================================================
# create_mappings_from_pydantic
# =====================================================================


class TestCreateMappingsFromPydantic:
    """create_mappings_from_pydantic()."""

    def test_basic(self):
        type_map, name_map = create_mappings_from_pydantic(CityModel)
        assert type_map == {
            "city_id": "String",
            "population": "Int32",
            "name": "String",
        }
        assert name_map == {
            "CityId": "city_id",
            "Population": "population",
            "name": "name",
        }

    def test_no_alias_uses_field_name(self):
        type_map, name_map = create_mappings_from_pydantic(HouseModel)
        # 'floors' has no alias -> key is field name itself
        assert "floors" in name_map and name_map["floors"] == "floors"

    def test_geometry_excluded(self):
        class WithGeom(BaseModel):
            id: str
            geometry: str

        _, name_map = create_mappings_from_pydantic(WithGeom, exclude_geometry=True)
        assert "geometry" not in name_map

    def test_geometry_included_by_default(self):
        class WithGeom(BaseModel):
            id: str
            geometry: str

        _, name_map = create_mappings_from_pydantic(WithGeom)
        assert "geometry" in name_map


# =====================================================================
# create_mappings_from_json
# =====================================================================


class TestCreateMappingsFromJson:
    """create_mappings_from_json()."""

    def test_first_layer_default(self):
        payload = {
            "layers": [
                {
                    "name": "cities",
                    "layerDefinition": {
                        "attributes": {
                            "CityId": {"type": "String"},
                            "name": {"type": "String"},
                        }
                    },
                }
            ]
        }
        type_map, name_map = create_mappings_from_json(payload, CityModel)
        assert "city_id" in type_map
        assert name_map["CityId"] == "city_id"

    def test_named_layer(self):
        payload = {
            "layers": [
                {"name": "wrong", "layerDefinition": {"attributes": {}}},
                {
                    "name": "cities",
                    "layerDefinition": {
                        "attributes": {"CityId": {"type": "String"}}
                    },
                },
            ]
        }
        type_map, _ = create_mappings_from_json(payload, CityModel, layer_name="cities")
        assert "city_id" in type_map

    def test_empty_layers_raises(self):
        with pytest.raises(ValueError, match="No layers"):
            create_mappings_from_json({"layers": []}, CityModel)

    def test_missing_named_layer_raises(self):
        payload = {
            "layers": [
                {"name": "other", "layerDefinition": {"attributes": {}}},
            ]
        }
        with pytest.raises(ValueError, match="not found"):
            create_mappings_from_json(payload, CityModel, layer_name="cities")

    def test_missing_layer_definition_raises(self):
        payload = {"layers": [{"name": "cities"}]}
        with pytest.raises(ValueError, match="Layer definition"):
            create_mappings_from_json(payload, CityModel)


# =====================================================================
# get_model_by_name
# =====================================================================


class TestGetModelByName:
    """get_model_by_name()."""

    def test_case_insensitive_lookup(self):
        result = get_model_by_name("citymodel", [CityModel, HouseModel])
        assert result is CityModel

    def test_exact_match(self):
        result = get_model_by_name("CityModel", [CityModel, HouseModel])
        assert result is CityModel

    def test_lowercase_match(self):
        result = get_model_by_name("housemodel", [CityModel, HouseModel])
        assert result is HouseModel

    def test_unknown_returns_none(self):
        result = get_model_by_name("unknown", [CityModel, HouseModel])
        assert result is None

    def test_empty_list_returns_none(self):
        assert get_model_by_name("CityModel", []) is None


# =====================================================================
# create_mappings_from_json_auto
# =====================================================================


class TestCreateMappingsFromJsonAuto:
    """create_mappings_from_json_auto()."""

    def test_auto_detect_model_by_layer_name(self):
        payload = {
            "layers": [
                {
                    "name": "CityModel",
                    "layerDefinition": {
                        "attributes": {"CityId": {"type": "String"}}
                    },
                }
            ]
        }
        model, type_map, name_map = create_mappings_from_json_auto(
            payload, [CityModel, HouseModel]
        )
        assert model is CityModel
        assert "city_id" in type_map

    def test_no_matching_model_returns_none(self):
        payload = {
            "layers": [
                {
                    "name": "UnknownLayer",
                    "layerDefinition": {"attributes": {}},
                }
            ]
        }
        model, type_map, name_map = create_mappings_from_json_auto(
            payload, [CityModel, HouseModel]
        )
        assert model is None
        assert type_map == {}
        assert name_map == {}

    def test_layer_index(self):
        payload = {
            "layers": [
                {"name": "ignored", "layerDefinition": {"attributes": {}}},
                {
                    "name": "HouseModel",
                    "layerDefinition": {
                        "attributes": {"HouseId": {"type": "String"}}
                    },
                },
            ]
        }
        model, _, _ = create_mappings_from_json_auto(
            payload, [CityModel, HouseModel], layer_index=1
        )
        assert model is HouseModel

    def test_empty_layers_raises(self):
        with pytest.raises(ValueError, match="No layers"):
            create_mappings_from_json_auto({"layers": []}, [CityModel])

    def test_layer_index_out_of_range(self):
        payload = {
            "layers": [{"name": "x", "layerDefinition": {"attributes": {}}}]
        }
        with pytest.raises(ValueError, match="out of range"):
            create_mappings_from_json_auto(payload, [CityModel], layer_index=5)
