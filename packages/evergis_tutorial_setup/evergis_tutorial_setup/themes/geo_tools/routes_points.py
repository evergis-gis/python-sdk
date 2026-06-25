# -*- coding: utf-8 -*-
"""``john_doe.evg_routes_points`` - Point target: route endpoints.

Style colours ``target`` role red, everything else (sources) blue,
and pins target points bigger.
"""

from __future__ import annotations

from typing import Optional

from pydantic import BaseModel, Field

from ..._config import LayerSchema


class RoutePoint(BaseModel):
    name: str = Field(...)
    category: Optional[str] = Field(None)
    role: str = Field(...)


STYLE = {
    "items": [
        {"type": "circle", "paint": {
            "circle-color": [
                "match", ["get", "role"], "target", "#e31a1c", "#1f78b4",
            ],
            "circle-radius": [
                "match", ["get", "role"], "target", 8, 5,
            ],
            "circle-stroke-color": "#ffffff", "circle-stroke-width": 1.5,
        }},
    ]
}

LAYER = LayerSchema(
    alias="route endpoints (target)",
    schema=RoutePoint,
    geometry_type="Point",
    client_style=STYLE,
)
