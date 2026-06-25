"""Read with EQL, then create a new layer from the result GeoDataFrame.

A shortcut path when you want a snapshot of a query: load it through
``eql_query_to_geodataframe`` (full pandas/geopandas in your hands),
do any local post-processing, then publish via ``gdf_to_layer`` +
``add_gdf_features_to_layer``. Different from ``create_query_layer``,
which keeps the EQL on the server.

Useful when the post-processing (cleaning, derived columns, joining
with non-EverGIS data) is easier in pandas than in EQL.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import add_layer_to_map, delete_resource
from evergis_tools.eql import eql_query_to_geodataframe
from evergis_tools.features import add_gdf_features_to_layer
from evergis_tools.layers import gdf_to_layer


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")

LAYER_SHORT = "from_eql_tall_buildings"
LAYER_ALIAS = "tall buildings (height > 50m)"
GEOMETRY_TYPE = "MultiPolygon"
SRID = 4326

QUERY = """
SELECT gid, name, class, height, floors, geom
FROM {SAMPLE_DATA_OWNER}.evg_overture_buildings
WHERE height IS NOT NULL AND height > 50
ORDER BY height DESC
LIMIT 200
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    target_layer = f"{username}.{RESOURCE_PREFIX}_{LAYER_SHORT}"
    target_parent = f"{username}/{PROJECT_PATH}/layers/results"

    delete_resource(client, target_layer, missing_ok=True)

    gdf = eql_query_to_geodataframe(QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client)
    gdf = gdf.set_crs(f"EPSG:{SRID}", allow_override=True)
    print(f"loaded {len(gdf)} buildings  (max height: {gdf['height'].max():.1f} m)")

    # Local enrichment - any pandas op fits here. Example: bin heights.
    gdf["height_band"] = (gdf["height"] // 25 * 25).astype(int)

    gdf_to_layer(
        client, gdf, target_layer,
        geometry_type=GEOMETRY_TYPE,
        parent_path=target_parent,
        layer_alias=LAYER_ALIAS,
        overwrite=True, log=False,
    )
    add_gdf_features_to_layer(
        client, gdf, target_layer,
        target_sr=SRID, geometry_type=GEOMETRY_TYPE, log=False,
    )
    add_layer_to_map(
        client, f"{username}.{RESOURCE_PREFIX}_map_layers", target_layer,
    )
    print(f"layer saved: {target_parent}/{target_layer}")
