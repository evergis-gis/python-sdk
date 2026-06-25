"""Synchronous N x M OD matrix via ``build_od_matrix_rest``.

Picks a handful of restaurants and a handful of metro stations from the
shared Overture demo layers, then asks the netEngine ``ODMatrix-rest``
worker for the car travel time in seconds between every (restaurant,
metro) pair. Unlike ``build_od_matrix`` (the layer-producing task), this
returns a plain DataFrame in-process - useful for ad-hoc analytics on
small point sets.
"""

import os

import pandas as pd

from evergis_tools import Client
from evergis_tools.features import query_layer_to_gdf
from evergis_tools.geo_tools import build_od_matrix_rest


SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")

N_RESTAURANTS = 5
N_METRO = 5


with Client() as client:
    # Shared Overture demo layers are read-only sample data under edu.
    places = f"{SAMPLE_DATA_OWNER}.evg_overture_places"
    metro  = f"{SAMPLE_DATA_OWNER}.evg_overture_metro_stations"

    restaurants = query_layer_to_gdf(
        client, places,
        conditions=["WHERE category = 'restaurant' AND confidence >= 0.95"],
        attributes=["gid", "name", "geom"],
        sort=["-confidence"],
        limit=N_RESTAURANTS,
    )
    stations = query_layer_to_gdf(
        client, metro,
        attributes=["gid", "name", "geom"],
        sort=["gid"],
        limit=N_METRO,
    )

    print(f"origins ({len(restaurants)} restaurants):")
    print(restaurants[["name"]].to_string(index=True))
    print(f"\ndestinations ({len(stations)} metro stations):")
    print(stations[["name"]].to_string(index=True))

    # GeoDataFrame inputs - ``build_od_matrix_rest`` accepts shapely
    # Points, (x, y) tuples or a GeoDataFrame; gid in the output reflects
    # the row index of each input.
    df = build_od_matrix_rest(
        client, restaurants, stations,
        transport_type="pedestrian",
        epsg_code=4326,
        seconds=True,
    )

    # Pivot into an N x M matrix for easy reading. The wrapper-returned
    # ``from`` / ``to`` indices match the input row order.
    matrix = (
        df.pivot(index="from", columns="to", values="distance")
          .rename(index=restaurants["name"], columns=stations["name"])
    )
    pd.set_option("display.width", 200)
    pd.set_option("display.max_columns", None)
    print(f"\nOD matrix (seconds, car, {len(restaurants)} x {len(stations)}):")
    print(matrix.round(0).astype("Int64").to_string())
