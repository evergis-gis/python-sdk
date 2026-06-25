# -*- coding: utf-8 -*-
"""``john_doe.evg_sandbox_polygon`` - empty Polygon for the
``add_layer_attributes`` example. No attributes beyond the implicit
``gid`` + ``geometry``; the example PATCH-extends the layer schema.
"""

from __future__ import annotations

from pydantic import BaseModel

from ..._config import LayerSchema


class _SandboxPolygon(BaseModel):
    """Empty schema - only implicit gid + geometry."""
    pass


LAYER = LayerSchema(
    alias="sandbox polygon (empty)",
    schema=_SandboxPolygon,
    geometry_type="Polygon",
    geometry_field="geometry",
    srid=4326,
)
