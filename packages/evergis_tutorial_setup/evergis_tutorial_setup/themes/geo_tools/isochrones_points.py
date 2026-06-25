# -*- coding: utf-8 -*-
"""``john_doe.evg_isochrones_points`` - Point target: origins of the isochrones."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from ..._config import LayerSchema


class IsochronePoint(BaseModel):
    name: str = Field(...)
    category: Optional[str] = Field(None)


STYLE = {
    "items": [
        {"type": "circle", "paint": {
            "circle-color": "#1f78b4", "circle-radius": 5,
            "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.5,
        }},
    ]
}

LAYER = LayerSchema(
    alias="isochrones origins (target)",
    schema=IsochronePoint,
    geometry_type="Point",
    client_style=STYLE,
)
