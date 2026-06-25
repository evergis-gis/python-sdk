# -*- coding: utf-8 -*-
"""Theme: ``layers`` - layer lifecycle (create / read / update / delete).

Two own seed layers under ``layers/data/``:

* ``evg_sandbox_polygon``      - empty Polygon for ``add_layer_attributes`` demo
* ``evg_places_update_layer``  - plain ``SELECT * FROM places`` for ``update_layer_eql``

The companion map composes its own seed + the ``stations`` slot from
``features`` (string-format demo) + the shared ``places_qry`` /
``overture_districts``.
"""

from ..._config import MapConfig, MapLayerRef, ThemeConfig

THEME = ThemeConfig(
    name="layers",
    alias="layers tutorial",
    depends_on=["shared", "features"],
    map=MapConfig(
        layers=[
            MapLayerRef(short="stations",             visible=True),
            MapLayerRef(short="places_update_layer",  visible=True),
            MapLayerRef(short="places_qry",           visible=False,
                        parameters={"@category": "%category"}),
            MapLayerRef(short="overture_districts",   visible=True),
        ],
    ),
)
