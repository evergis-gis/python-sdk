"""Create a virtual query layer (no physical table).

Same JOIN as ``create_query_layer.py`` but with ``create_table=False`` -
the layer does NOT copy rows into its own table. Every read reissues
the query against the source layers, so the result always reflects
the current state of ``evg_overture_places`` / ``evg_overture_districts``,
at the cost of read latency.

Use a materialized layer (``create_table=True``) for stable analytics
snapshots, and a virtual layer when freshness matters more than speed.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import add_layer_to_map, delete_resource
from evergis_tools.layers import create_query_layer


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")

LAYER_SHORT = "qry_pois_in_divisions_virtual"
LAYER_ALIAS = "POIs in divisions (virtual)"
GEOMETRY_TYPE = "Point"
SRID = 4326

QUERY = """
SELECT
    p.name AS poi_name,
    p.category,
    d.name AS division,
    p.geom
FROM {SAMPLE_DATA_OWNER}.evg_overture_places AS p
JOIN {SAMPLE_DATA_OWNER}.evg_overture_districts AS d
    ON ST_Within(p.geom, d.geom)
"""


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
        create_table=False,
        overwrite=True, log=False,
    )
    add_layer_to_map(
        client, f"{username}.{RESOURCE_PREFIX}_map_layers", target_layer,
    )
    print(f"layer saved (virtual, no physical table): {target_parent}/{target_layer}")
