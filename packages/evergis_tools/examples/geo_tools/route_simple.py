"""Build a pedestrian route between two POIs and plot the result.

Picks two POIs from the demo layer ``evg_overture_places`` (first two
``train_station`` points), builds a walking route via ``build_route``
and plots the resulting line with both endpoints.
"""

import geopandas as gpd
import matplotlib.pyplot as plt

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_geodataframe
from evergis_tools.geo_tools import build_route


QUERY = """
SELECT name, geom
FROM {SAMPLE_DATA_OWNER}.evg_overture_places
WHERE category = 'train_station'
LIMIT 2
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    points = eql_query_to_geodataframe(QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client)
    if len(points) < 2:
        raise SystemExit("need at least two train_station POIs")

    start, end = points.geometry.iloc[0], points.geometry.iloc[1]
    start_name = points.iloc[0]["name"] or "(unnamed)"
    end_name = points.iloc[1]["name"] or "(unnamed)"
    print(f"from: {start_name}\nto:   {end_name}")

    route = build_route(client, start, end, sr_in=4326, sr_out=4326)
    print(f"route: {route.geom_type}")

    route_gdf = gpd.GeoDataFrame(geometry=[route], crs="EPSG:4326")

    fig, ax = plt.subplots(figsize=(8, 8))
    route_gdf.plot(ax=ax, color="tab:blue", linewidth=2)
    points.plot(ax=ax, color="tab:red", markersize=80, zorder=5)
    ax.set_title(f"Walking route: {start_name} -> {end_name}")
    ax.set_axis_off()
    plt.show()
