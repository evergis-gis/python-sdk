"""Create a materialized query layer over demo data with a JOIN.

Joins ``evg_overture_places`` with ``evg_overture_districts`` so every
POI carries the name of the division it sits in. The result is
published as a new ``Point`` query layer at
``{PROJECT_PATH}/layers/results/<username>.evg_pois_in_divisions``.

``create_table=True`` (default for this example) materializes the
result into a physical table - the layer keeps its rows even if the
source layers change. For a non-materialized variant see
``create_query_layer_virtual.py``.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import add_layer_to_map, delete_resource
from evergis_tools.layers import create_query_layer


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")

LAYER_SHORT = "qry_pois_in_divisions"
LAYER_ALIAS = "POIs tagged with division"
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
        overwrite=True, log=False,
    )
    add_layer_to_map(
        client, f"{username}.{RESOURCE_PREFIX}_map_layers", target_layer,
    )
    print(f"layer saved: {target_parent}/{target_layer}")
