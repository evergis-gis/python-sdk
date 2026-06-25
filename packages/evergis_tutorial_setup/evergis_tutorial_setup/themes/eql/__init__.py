# -*- coding: utf-8 -*-
"""Theme: ``eql`` - read-only EQL queries against the seed demo layers.

Examples only read; nothing is published. The companion map shows the
full set of seed layers (places, districts, buildings, streets) plus
both shared wrapper layers (``places_qry``, ``distr_poi_count``) so
EQL examples have something visual to spot-check against.
"""

from ..._config import MapConfig, MapLayerRef, ThemeConfig

THEME = ThemeConfig(
    name="eql",
    alias="eql tutorial",
    depends_on=["shared"],
    map=MapConfig(
        layers=[
            MapLayerRef(short="distr_poi_count",    visible=False,
                        parameters={"@category": "%category"}),
            MapLayerRef(short="places_qry",         visible=True,
                        parameters={"@category": "%category"}),
            MapLayerRef(short="overture_streets",   visible=False),
            MapLayerRef(short="overture_buildings", visible=False),
            MapLayerRef(short="overture_districts", visible=True),
        ],
    ),
)
