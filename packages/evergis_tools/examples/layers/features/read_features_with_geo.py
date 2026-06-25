"""Read a Point layer into a GeoDataFrame and plot it.

``query_layer_to_gdf`` resolves the geometry column and returns a
``geopandas.GeoDataFrame`` with ``crs`` set - ready for ``.plot()`` or
spatial joins.

Source: ``{SAMPLE_DATA_OWNER}.evg_overture_metro_stations`` (Moscow Metro stations,
published by ``sample-data pipeline`` under
``EverGIS Resources/Sample data & maps/overture/``).
"""

import matplotlib.pyplot as plt

import os
from evergis_tools import Client
from evergis_tools.features import query_layer_to_gdf


SOURCE_LAYER_SHORT = "evg_overture_metro_stations"


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    source_layer = f"{SAMPLE_DATA_OWNER}.{SOURCE_LAYER_SHORT}"

    gdf = query_layer_to_gdf(
        client, layer_name=source_layer,
        # Geometry column on Overture layers is ``geom`` (not ``geometry``);
        # include it explicitly so the server returns the geometry payload.
        attributes=["gid", "name", "category", "brand", "geom"],
        sort=["gid"],
    )
    print(f"layer:   {source_layer}")
    print(f"rows:    {len(gdf)}  crs: {gdf.crs}")
    print(gdf.drop(columns="geometry").head(10).to_string(index=False))

    ax = gdf.plot(figsize=(9, 9), markersize=20, color="#1f78b4")
    ax.set_title(source_layer)
    ax.set_axis_off()
    plt.show()
