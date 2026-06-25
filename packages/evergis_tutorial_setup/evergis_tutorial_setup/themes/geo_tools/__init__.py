# -*- coding: utf-8 -*-
"""Theme: ``geo_tools`` - isochrones, routes, voronoi.

Six empty target layers under ``geo_tools/data/`` the examples
populate (clear + compute + insert). The examples are about the
calculation; the pipeline pre-creates the targets so each script
stays focused on the algorithm.

* ``evg_isochrones``        - MultiPolygon
* ``evg_isochrones_points`` - Point
* ``evg_routes``            - MultiLineString
* ``evg_routes_points``     - Point
* ``evg_voronoi``           - MultiPolygon
* ``evg_voronoi_points``    - Point

Re-running ``themes geo_tools --force`` resets all six to empty.
"""

from ..._config import MapConfig, MapLayerRef, ThemeConfig

THEME = ThemeConfig(
    name="geo_tools",
    alias="geo_tools tutorial",
    depends_on=["shared"],
    map=MapConfig(
        layers=[
            MapLayerRef(short="isochrones_points", visible=False),
            MapLayerRef(short="isochrones",        visible=False),
            MapLayerRef(short="routes_points",     visible=False),
            MapLayerRef(short="routes",            visible=False),
            MapLayerRef(short="voronoi_points",    visible=False),
            MapLayerRef(short="voronoi",           visible=False),
            MapLayerRef(short="places_qry",        visible=True,
                        parameters={"@category": "%category"}),
            MapLayerRef(short="overture_districts", visible=True),
        ],
    ),
)
