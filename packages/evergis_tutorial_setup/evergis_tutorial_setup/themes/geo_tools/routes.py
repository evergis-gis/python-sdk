# -*- coding: utf-8 -*-
"""``john_doe.evg_routes`` - MultiLineString target for routing results."""

from __future__ import annotations

from pydantic import BaseModel, Field

from ..._config import LayerSchema


class Route(BaseModel):
    from_name: str = Field(...)
    to_name: str = Field(...)
    length_m: float = Field(...)


STYLE = {
    "items": [
        {"type": "line", "paint": {
            "line-color": "#e31a1c", "line-width": 3, "line-opacity": 0.85,
        }},
    ]
}

LAYER = LayerSchema(
    alias="routes (target)",
    schema=Route,
    geometry_type="MultiLineString",
    client_style=STYLE,
)
