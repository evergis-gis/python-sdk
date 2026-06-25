# -*- coding: utf-8 -*-
"""``john_doe.evg_voronoi_points`` - Point target: voronoi generators."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from ..._config import LayerSchema


class VoronoiPoint(BaseModel):
    name: Optional[str] = Field(None)
    category: Optional[str] = Field(None)


STYLE = {
    "items": [
        {"type": "circle", "paint": {
            "circle-color": "#000000", "circle-radius": 3,
            "circle-stroke-color": "#ffffff", "circle-stroke-width": 1,
        }},
    ]
}

LAYER = LayerSchema(
    alias="voronoi generators (target)",
    schema=VoronoiPoint,
    geometry_type="Point",
    client_style=STYLE,
)
