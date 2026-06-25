# -*- coding: utf-8 -*-
"""``john_doe.evg_places_qry`` - thin virtual wrapper over Overture places.

Three optional ``${isset:@x, {...}}`` filters (category, min_conf,
name_like) let companion maps wire a dropdown / search input without
publishing a new variant of the layer for each filter combination.
"""

from ..._config import EqlParam, LayerQuery


STYLE = {
    "items": [
        {
            "type": "circle",
            "paint": {
                "circle-radius": 4,
                "circle-color": "#3182bd",
                "circle-stroke-color": "#1f4d80",
                "circle-stroke-width": 1,
                "circle-opacity": 0.85,
            },
        }
    ],
}

EQL = """
SELECT * FROM ${places}
WHERE TRUE
${isset:@category,  { AND category = @category }}
${isset:@min_conf,  { AND confidence >= @min_conf }}
${isset:@name_like, { AND name LIKE concat('%', @name_like, '%') }}
""".strip()


LAYER = LayerQuery(
    alias="places (parametrised wrapper)",
    eql=EQL,
    eql_refs={"places": "overture_places"},
    eql_parameters={
        "@category":  EqlParam("String"),
        "@min_conf":  EqlParam("Double"),
        "@name_like": EqlParam("String"),
    },
    geometry_type="Point",
    geometry_attribute="geom",
    client_style=STYLE,
)
