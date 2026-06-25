# -*- coding: utf-8 -*-
"""``john_doe.evg_voronoi`` - MultiPolygon target for Voronoi cells."""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from ..._config import LayerSchema


class VoronoiCell(BaseModel):
    name: Optional[str] = Field(None)
    category: Optional[str] = Field(None)


STYLE = {
    "items": [
        {"type": "fill", "paint": {
            "fill-color": [
                "match", ["get", "category"], "restaurant", "#fb9a99", "#cccccc",
            ],
            "fill-opacity": 0.5,
        }},
        {"type": "line", "paint": {"line-color": "#ffffff", "line-width": 0.8}},
    ]
}

LAYER = LayerSchema(
    alias="voronoi cells (target)",
    schema=VoronoiCell,
    geometry_type="MultiPolygon",
    client_style=STYLE,
)
