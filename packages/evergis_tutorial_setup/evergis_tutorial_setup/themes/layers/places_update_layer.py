# -*- coding: utf-8 -*-
"""``john_doe.evg_places_update_layer`` - plain ``SELECT * FROM places``
virtual layer for the ``update_layer_eql`` example.

Intentionally trivial: no JOINs, no parameters. The example enriches
the EQL in-place (adds parameters + a JOIN with districts), so the seed
must start from the minimal shape. Re-run ``themes layers --force`` to
reset.
"""

from __future__ import annotations

from ..._config import LayerQuery


LAYER = LayerQuery(
    alias="places (update_layer tutorial)",
    eql="SELECT * FROM ${places}",
    eql_refs={"places": "overture_places"},
    geometry_type="Point",
    geometry_attribute="geom",
)
