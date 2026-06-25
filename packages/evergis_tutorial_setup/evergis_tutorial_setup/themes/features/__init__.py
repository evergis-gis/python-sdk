# -*- coding: utf-8 -*-
"""Theme: ``features`` - work with layer features (add / read / edit / delete).

Two seed layers under ``features/data/``:

* ``evg_stations`` (Point, ``WeatherStation`` schema, 4 fixture rows)
* ``evg_logs``     (table, ``MeasurementLog`` schema, 4 fixture rows)

Re-running ``themes features --force`` resets both seeds to a known
state. Examples live under ``packages/evergis_tools/examples/layers/features/``
and are mirrored into ``features/scripts/`` (note the override of
``mirror_source`` - the examples directory is nested for historical reasons).

No ``results/`` slot: the features examples mutate the seed layers in
place rather than publishing new ones.
"""

from ..._config import MapConfig, MapLayerRef, ThemeConfig

THEME = ThemeConfig(
    name="features",
    alias="features tutorial",
    depends_on=["shared"],
    folders=("scripts", "data"),
    mirror_source="layers/features",
    map=MapConfig(
        layers=[
            MapLayerRef(short="stations",          visible=True),
            MapLayerRef(short="places_qry",        visible=True,
                        parameters={"@category": "%category"}),
            MapLayerRef(short="overture_districts", visible=True),
        ],
    ),
)
