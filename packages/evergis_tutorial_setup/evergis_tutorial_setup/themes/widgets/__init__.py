# -*- coding: utf-8 -*-
"""Theme: ``widgets`` - feature card / edit form widgets.

Widget configuration is layer-scoped, so the companion map shows the
parametrised places wrapper (where widgets light up when the user
clicks a feature) plus metro stations and districts for context.
Has an extra ``images/`` slot for icons referenced by widget configs.
"""

from ..._config import MapConfig, MapLayerRef, ThemeConfig

THEME = ThemeConfig(
    name="widgets",
    alias="widgets tutorial",
    depends_on=["shared"],
    folders=("scripts", "data", "results", "images"),
    map=MapConfig(
        layers=[
            MapLayerRef(short="places_qry",              visible=True,
                        parameters={"@category": "%category"}),
            MapLayerRef(short="overture_metro_stations", visible=False),
            MapLayerRef(short="overture_districts",      visible=True),
        ],
    ),
)
