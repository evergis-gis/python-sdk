# -*- coding: utf-8 -*-
"""``john_doe.evg_isochrones`` - MultiPolygon target for isochrone polygons."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..._config import LayerSchema


class IsochronePoly(BaseModel):
    name: str = Field(...)
    duration_min: int = Field(...)


STYLE = {
    "items": [
        {"type": "fill", "paint": {"fill-color": "#1f78b4", "fill-opacity": 0.25}},
        {"type": "line", "paint": {"line-color": "#1f78b4", "line-width": 1.5}},
    ]
}

LAYER = LayerSchema(
    alias="isochrones (target)",
    schema=IsochronePoly,
    geometry_type="MultiPolygon",
    client_style=STYLE,
)
