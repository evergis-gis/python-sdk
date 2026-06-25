# -*- coding: utf-8 -*-
"""Calculated attribute helper.

A calculated attribute carries an EQL ``expression`` that the server
evaluates per feature. The value is materialised into a physical
column (``columnName``), so it can be queried and indexed like any
other attribute.

Usage:

.. code-block:: python

    from evergis_tools.attribute_types import CalculatedAttribute
    from evergis_tools.layers import add_layer_attribute

    add_layer_attribute(
        client, "john_doe.my_layer",
        CalculatedAttribute(
            attributeName="density",
            type="Double",
            expression="population / NULLIF(area_km2, 0)",
            alias="Population density",
        ),
    )

Notes:

* ``columnName`` defaults to ``attributeName`` - the current server
  rejects ``PATCH /layers/{name}`` with HTTP 400 if it is missing,
  and ``POST /layers`` quietly fills it in itself. A true "virtual"
  (compute-on-read) mode is not exposed by the API today.
* ``aggregation`` is only needed when the expression aggregates child
  rows (e.g. ``SUM(weight)`` over a referenced layer). For row-wise
  expressions leave it at the default ``None``.
"""

from __future__ import annotations

from typing import Literal

from pydantic import ConfigDict, Field, model_validator

from evergis_api.schemas import (
    AttributeConfigurationType,
    CalculatedAttributeConfigurationDc,
)


class CalculatedAttribute(CalculatedAttributeConfigurationDc):
    """Schema entry for a calculated attribute.

    Pre-fills ``attributeConfigurationType=Calculated`` and defaults
    ``columnName`` to ``attributeName`` so the caller only supplies
    ``attributeName``, ``type``, ``expression`` (and an optional
    ``alias`` / ``aggregation`` / standard flags).

    The instance still *is* a
    :class:`CalculatedAttributeConfigurationDc`, so it can be appended
    directly to ``AttributesConfigurationDc.attributes``.
    """

    attribute_configuration_type: Literal[AttributeConfigurationType.CALCULATED] = Field(
        default=AttributeConfigurationType.CALCULATED,
        alias="attributeConfigurationType",
    )

    model_config = ConfigDict(
        extra="forbid",
        validate_assignment=True,
        use_enum_values=True,
        populate_by_name=True,
    )

    @model_validator(mode="after")
    def _finalize(self) -> "CalculatedAttribute":
        if self.columnName is None:
            self.columnName = self.attributeName

        # The generated client serializes patches with
        # ``model_dump(exclude_unset=True)`` and the parent ``attributes``
        # field is an un-discriminated Union, so the literal-locked
        # discriminator and the defaulted ``columnName`` would silently
        # drop out without these explicit marks.
        self.__pydantic_fields_set__.update(
            {"attribute_configuration_type", "columnName"}
        )
        return self


__all__ = ["CalculatedAttribute"]
