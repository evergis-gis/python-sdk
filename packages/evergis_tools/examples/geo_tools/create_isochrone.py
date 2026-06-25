"""Build isochrones around POIs and write them into a pre-created layer.

For a sample of POIs (the first 10 ``train_station`` points in
``evg_overture_places``) ``build_isochrone`` produces a 10-minute
pedestrian isochrone. The polygons are appended to the
**pipeline-provisioned** target layer ``evg_isochrones`` (and the
source POIs to the companion ``evg_isochrones_points``); the
example focuses on the calculation, not on layer plumbing.

Run the seed once:

    .venv/bin/python -m evergis_tutorial_setup themes geo_tools

Re-run this script clears the target layers first - safe and
idempotent. To restore the seed completely:

    python -m evergis_tutorial_setup themes geo_tools --force

The simpler read-only variant is ``isochrone_simple.py``.
"""

import time

import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_geodataframe
from evergis_tools.features import (
    add_gdf_features_to_layer,
    delete_features_by_condition,
)
from evergis_tools.geo_tools import build_isochrone


SRID = 4326

POI_CATEGORY = "train_station"
SAMPLE_SIZE = 10
DURATION_MIN = 10

TARGET_LAYER       = "evg_isochrones"
TARGET_POINTS      = "evg_isochrones_points"
TARGET_GEOMETRY    = "MultiPolygon"
POINTS_GEOMETRY    = "Point"

POINTS_QUERY = """
SELECT name, category, geom
FROM {SAMPLE_DATA_OWNER}.evg_overture_places
WHERE category = '{category}'
LIMIT {limit}
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    target_layer = f"{username}.{TARGET_LAYER}"
    points_layer = f"{username}.{TARGET_POINTS}"

    # Reset both targets so re-runs produce the same result.
    delete_features_by_condition(client, target_layer, "WHERE gid > 0")
    delete_features_by_condition(client, points_layer, "WHERE gid > 0")

    points = eql_query_to_geodataframe(
        POINTS_QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, 
            username=username, category=POI_CATEGORY, limit=SAMPLE_SIZE,
        ),
        client,
    )
    print(f"sample: {len(points)} points")

    rows = []
    started = time.time()
    for _, row in points.iterrows():
        iso = build_isochrone(
            client, row.geometry, duration=DURATION_MIN,
            sr_in=SRID, sr_out=SRID,
        )
        if iso is None:
            print(f"  skip {row['name']}: no isochrone")
            continue
        # Server target is MultiPolygon; promote single Polygons.
        if isinstance(iso, Polygon):
            iso = MultiPolygon([iso])
        rows.append({
            "name": row["name"],
            "duration_min": DURATION_MIN,
            "geometry": iso,
        })
        print(f"  {row['name']}")

    print(f"\nbuilt {len(rows)} isochrones in {time.time() - started:.1f}s")

    out = gpd.GeoDataFrame(rows, crs=f"EPSG:{SRID}")
    add_gdf_features_to_layer(
        client, out, target_layer,
        target_sr=SRID, geometry_type=TARGET_GEOMETRY, log=False,
    )
    add_gdf_features_to_layer(
        client, points, points_layer,
        target_sr=SRID, geometry_type=POINTS_GEOMETRY, log=False,
    )
    print(f"\nwrote {len(out)} isochrones + {len(points)} source points")
