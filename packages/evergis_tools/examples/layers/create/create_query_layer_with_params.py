"""Create a query layer with bound EQL parameters.

Uses ``@`` parameter binding to filter ``evg_overture_buildings`` by
``class``. Try changing ``BUILDING_CLASS`` (apartments / commercial /
residential / hotel ...) - the same query template covers every case
without string-concatenating user input into the SQL.

Layer is published at
``{PROJECT_PATH}/layers/results/<username>.evg_buildings_by_class``.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import add_layer_to_map, delete_resource
from evergis_tools.layers import create_query_layer


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")

LAYER_SHORT = "qry_buildings_by_class"
LAYER_ALIAS = "buildings filtered by class"
GEOMETRY_TYPE = "MultiPolygon"
SRID = 4326

BUILDING_CLASS = "apartments"  # try: commercial / residential / hotel / industrial

QUERY = """
SELECT gid, name, class, subtype, height, floors, geom
FROM {SAMPLE_DATA_OWNER}.evg_overture_buildings
WHERE class = @building_class
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
        eql_parameters={"@building_class": BUILDING_CLASS},
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
    print(f"layer saved: {target_parent}/{target_layer}  (class={BUILDING_CLASS})")
