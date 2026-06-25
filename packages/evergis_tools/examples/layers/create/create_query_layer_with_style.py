"""Create a query layer with a Mapbox GL style applied at creation.

Same source as ``create_query_layer.py`` (POIs tagged with division),
but with ``client_style`` so the layer renders with category-based
colors as soon as it appears on a map. The same style can be updated
later via ``update_layer_style`` (see ``examples/layers/update``).
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import add_layer_to_map, delete_resource
from evergis_tools.layers import create_query_layer


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")

LAYER_SHORT = "qry_pois_styled"
LAYER_ALIAS = "POIs styled by category"
GEOMETRY_TYPE = "Point"
SRID = 4326

QUERY = """
SELECT
    p.gid,
    p.name AS poi_name,
    p.category,
    d.name AS division,
    p.geom
FROM {SAMPLE_DATA_OWNER}.evg_overture_places AS p
JOIN {SAMPLE_DATA_OWNER}.evg_overture_districts AS d
    ON ST_Within(p.geom, d.geom)
"""

STYLE = {
    "items": [
        {
            "type": "circle",
            "paint": {
                "circle-color": [
                    "match", ["get", "category"],
                    "restaurant", "#e31a1c",
                    "train_station", "#1f78b4",
                    "hospital", "#33a02c",
                    "#999999",
                ],
                "circle-radius": 5,
                "circle-stroke-color": "#ffffff",
                "circle-stroke-width": 1,
            },
        },
    ]
}


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    target_layer = f"{username}.{RESOURCE_PREFIX}_{LAYER_SHORT}"
    target_parent = f"{username}/{PROJECT_PATH}/layers/results"

    delete_resource(client, target_layer, missing_ok=True)

    create_query_layer(
        client=client,
        layer_name=target_layer,
        eql_query=QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username),
        layer_alias=LAYER_ALIAS,
        parent_path=target_parent,
        geometry_type=GEOMETRY_TYPE,
        srid=SRID,
        create_table=True,
        client_style=STYLE,
        overwrite=True, log=False,
    )
    add_layer_to_map(
        client, f"{username}.{RESOURCE_PREFIX}_map_layers", target_layer,
    )
    print(f"layer saved: {target_parent}/{target_layer}")
