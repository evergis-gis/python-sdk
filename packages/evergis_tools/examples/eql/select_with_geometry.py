"""Run a SELECT EQL query with a filter and get a GeoDataFrame.

``eql_query_to_geodataframe`` adds the resolved geometry column
(decoded to Shapely shapes) and sets the GeoDataFrame's CRS.

The example fetches the ten tallest buildings (``height`` is in
metres) and prints geometry bounds for each.

Reads from the seed layer ``{SAMPLE_DATA_OWNER}.evg_overture_buildings``.
"""

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_geodataframe


QUERY = """
SELECT name, height, floors, geom
FROM {SAMPLE_DATA_OWNER}.evg_overture_buildings
WHERE height > 50
ORDER BY height DESC
LIMIT 10
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    gdf = eql_query_to_geodataframe(QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client)

    print(f"rows: {len(gdf)}  CRS: {gdf.crs}")
    for _, row in gdf.iterrows():
        bounds = row.geometry.bounds
        label = row["name"] or "(unnamed)"
        print(
            f"  {label:35s}  height={row.height:>5.1f}m  "
            f"floors={row.floors!s:>4}  bounds=({bounds[0]:.4f}, {bounds[1]:.4f})"
        )
