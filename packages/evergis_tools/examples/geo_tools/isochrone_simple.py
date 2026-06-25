"""Build a 10-minute walking isochrone around a POI and plot the result.

Picks the first ``train_station`` POI from the demo layer
``evg_overture_places``, builds a pedestrian isochrone via
``build_isochrone``, then renders the isochrone polygon with the
start point on top using ``GeoDataFrame.plot``.
"""

import geopandas as gpd
import matplotlib.pyplot as plt

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_geodataframe
from evergis_tools.geo_tools import build_isochrone


QUERY = """
SELECT name, geom
FROM {SAMPLE_DATA_OWNER}.evg_overture_places
WHERE category = 'train_station'
LIMIT 1
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    points = eql_query_to_geodataframe(QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username), client, geometry_field='geom')
    if points.empty:
        raise SystemExit("no train_station POI found in evg_overture_places")

    start = points.geometry.iloc[0]
    label = points.iloc[0]["name"] or "(unnamed)"
    print(f"start point: {label}  ({start.x:.4f}, {start.y:.4f})")

    isochrone = build_isochrone(
        client, start, duration=10, sr_in=4326, sr_out=4326
    )
    print(f"isochrone: {isochrone.geom_type}")

    iso_gdf = gpd.GeoDataFrame(
        {"name": [label]}, geometry=[isochrone], crs="EPSG:4326"
    )

    fig, ax = plt.subplots(figsize=(8, 8))
    iso_gdf.plot(ax=ax, alpha=0.4, color="tab:blue", edgecolor="tab:blue")
    points.plot(ax=ax, color="tab:red", markersize=80, zorder=5)
    ax.set_title(f"10-min walking isochrone - {label}")
    ax.set_axis_off()
    plt.show()
