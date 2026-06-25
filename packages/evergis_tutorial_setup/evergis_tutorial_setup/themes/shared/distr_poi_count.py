# -*- coding: utf-8 -*-
"""``john_doe.evg_distr_poi_count`` - choropleth-ready POI count per district.

CTE + LEFT JOIN demo: counts POIs that fall inside each Moscow district
geometry, optionally filtered by ``@category``. Used as a backing layer
for choropleth-style examples in ``eql`` / ``widgets``.
"""

from ..._config import EqlParam, LayerQuery


# Sequential blue step-binned fill; light-to-dark = low-to-high POI count.
STYLE = {
    "items": [
        {
            "type": "fill",
            "paint": {
                "fill-color": [
                    "step", ["get", "n"],
                    "#f7fbff",
                    100,  "#deebf7",
                    500,  "#c6dbef",
                    1000, "#9ecae1",
                    2000, "#6baed6",
                    3000, "#4292c6",
                    5000, "#2171b5",
                    8000, "#08519c",
                ],
                "fill-opacity": 0.7,
                "fill-outline-color": "#ffffff",
            },
        },
        {
            "type": "line",
            "paint": {"line-color": "#ffffff", "line-width": 0.5},
        },
    ],
}

EQL = """
WITH poi AS (
    SELECT geom FROM ${places}
    WHERE TRUE
        ${isset:@category, { AND category = @category }}
)
SELECT
    d.gid,
    d.name AS district,
    COUNT(p.geom)::int AS n,
    d.geom
FROM ${districts} AS d
LEFT JOIN poi AS p ON ST_Within(p.geom, d.geom)
GROUP BY d.gid, d.name, d.geom
ORDER BY n DESC
""".strip()


LAYER = LayerQuery(
    alias="POI count per district (choropleth)",
    eql=EQL,
    eql_refs={"places": "overture_places", "districts": "overture_districts"},
    eql_parameters={"@category": EqlParam("String")},
    geometry_type="MultiPolygon",
    geometry_attribute="geom",
    client_style=STYLE,
)
