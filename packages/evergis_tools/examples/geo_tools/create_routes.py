"""Build pedestrian routes between POIs and write them into pre-created layers.

For 10 ``train_station`` source POIs and one ``hospital`` target,
``build_route`` produces pedestrian paths. Routes are appended to the
**pipeline-provisioned** target layer ``evg_routes``; source/target
markers are appended to the ``_points`` companion with a ``role``
attribute that the map style colors differently.

Run the seed once:

    .venv/bin/python -m evergis_tutorial_setup themes geo_tools

Re-runs clear both targets first - safe and idempotent. To restore
the seed completely:

    python -m evergis_tutorial_setup themes geo_tools --force

The simpler read-only variant is ``route_simple.py``.
"""

import geopandas as gpd
import pandas as pd
from shapely.geometry import LineString, MultiLineString

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_geodataframe
from evergis_tools.features import (
    add_gdf_features_to_layer,
    delete_features_by_condition,
)
from evergis_tools.geo_tools import build_route


SRID = 4326
METRIC_SRID = 3857  # Web Mercator - used to approximate route length in metres

SOURCE_CATEGORY = "train_station"
TARGET_CATEGORY = "hospital"
SAMPLE_SIZE = 10

ROLE_SOURCE = "source"
ROLE_TARGET = "target"

TARGET_LAYER    = "evg_routes"
TARGET_POINTS   = "evg_routes_points"
TARGET_GEOMETRY = "MultiLineString"
POINTS_GEOMETRY = "Point"

SOURCES_QUERY = """
SELECT name, category, geom
FROM {SAMPLE_DATA_OWNER}.evg_overture_places
WHERE category = '{category}'
LIMIT {limit}
"""

TARGET_QUERY = """
SELECT name, category, geom
FROM {SAMPLE_DATA_OWNER}.evg_overture_places
WHERE category = '{category}'
LIMIT 1
"""


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    target_layer = f"{username}.{TARGET_LAYER}"
    points_layer = f"{username}.{TARGET_POINTS}"

    delete_features_by_condition(client, target_layer, "WHERE gid > 0")
    delete_features_by_condition(client, points_layer, "WHERE gid > 0")

    sources = eql_query_to_geodataframe(
        SOURCES_QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, 
            username=username, category=SOURCE_CATEGORY, limit=SAMPLE_SIZE,
        ),
        client,
    )
    targets = eql_query_to_geodataframe(
        TARGET_QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username, category=TARGET_CATEGORY),
        client,
    )
    if targets.empty:
        raise SystemExit(f"no '{TARGET_CATEGORY}' POI found - pick another category")
    target = targets.iloc[0]
    print(f"target: {target['name']}  sources: {len(sources)}")

    rows = []
    for _, row in sources.iterrows():
        route = build_route(
            client, row.geometry, target.geometry,
            sr_in=SRID, sr_out=SRID,
        )
        if route is None:
            print(f"  skip {row['name']}: no route")
            continue
        if isinstance(route, LineString):
            route = MultiLineString([route])
        length_m = float(
            gpd.GeoSeries([route], crs=f"EPSG:{SRID}")
            .to_crs(METRIC_SRID).length.iloc[0]
        )
        rows.append({
            "from_name": row["name"],
            "to_name": target["name"],
            "length_m": round(length_m, 1),
            "geometry": route,
        })
        print(f"  {row['name']} -> {target['name']}: {length_m:,.0f} m")

    out = gpd.GeoDataFrame(rows, crs=f"EPSG:{SRID}")
    add_gdf_features_to_layer(
        client, out, target_layer,
        target_sr=SRID, geometry_type=TARGET_GEOMETRY, log=False,
    )

    sources_tagged = sources.assign(role=ROLE_SOURCE)
    targets_tagged = targets.assign(role=ROLE_TARGET)
    points_out = gpd.GeoDataFrame(
        pd.concat([sources_tagged, targets_tagged], ignore_index=True),
        crs=f"EPSG:{SRID}",
    )
    add_gdf_features_to_layer(
        client, points_out, points_layer,
        target_sr=SRID, geometry_type=POINTS_GEOMETRY, log=False,
    )
    print(f"\nwrote {len(out)} routes + {len(points_out)} markers")
