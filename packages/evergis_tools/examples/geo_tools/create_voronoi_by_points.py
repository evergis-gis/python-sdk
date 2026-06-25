"""Build Voronoi cells around POIs and write them into pre-created layers.

Loads all restaurants inside the Tsentralny administrative division
from ``evg_overture_places``, builds Voronoi cells clipped to the
division boundary via ``create_voronoi_with_attributes``, and appends
them to the **pipeline-provisioned** target layer ``evg_voronoi``.
The source restaurants land in ``evg_voronoi_points``.

Run the seed once:

    .venv/bin/python -m evergis_tutorial_setup themes geo_tools

Re-runs clear both targets first - safe and idempotent. To restore
the seed completely:

    python -m evergis_tutorial_setup themes geo_tools --force

The simpler read-only variant is ``voronoi_simple.py``.
"""

import geopandas as gpd
from shapely.geometry import MultiPolygon, Polygon

import os
from evergis_tools import Client
from evergis_tools.eql import eql_query_to_geodataframe
from evergis_tools.features import (
    add_gdf_features_to_layer,
    delete_features_by_condition,
)
from evergis_tools.geo_tools import create_voronoi_with_attributes


SRID = 4326

DIVISION_NAME = "Центральный"
POI_CATEGORY = "restaurant"

# Attribute columns carried from the source POIs into the Voronoi layer.
# Used as the projection in the SELECT below, the attribute_columns argument
# of the voronoi builder, and the column subset of the output GeoDataFrame.
POI_ATTRS = ["name", "category"]

TARGET_LAYER    = "evg_voronoi"
TARGET_POINTS   = "evg_voronoi_points"
TARGET_GEOMETRY = "MultiPolygon"
POINTS_GEOMETRY = "Point"

DIVISION_QUERY = """
SELECT name, geom FROM {SAMPLE_DATA_OWNER}.evg_overture_districts
WHERE name = '{division}'
"""

POINTS_QUERY = """
WITH d AS (
    SELECT geom FROM {SAMPLE_DATA_OWNER}.evg_overture_districts WHERE name = '{division}'
)
SELECT {attrs}, p.geom AS geometry
FROM {SAMPLE_DATA_OWNER}.evg_overture_places AS p
JOIN d ON ST_Within(p.geom, d.geom)
WHERE p.category = '{category}'
"""


def _ensure_multipolygon(geom):
    if isinstance(geom, Polygon):
        return MultiPolygon([geom])
    return geom


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    target_layer = f"{username}.{TARGET_LAYER}"
    points_layer = f"{username}.{TARGET_POINTS}"

    delete_features_by_condition(client, target_layer, "WHERE gid > 0")
    delete_features_by_condition(client, points_layer, "WHERE gid > 0")

    division = eql_query_to_geodataframe(
        DIVISION_QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, username=username, division=DIVISION_NAME),
        client,
    )
    points = eql_query_to_geodataframe(
        POINTS_QUERY.format(SAMPLE_DATA_OWNER=SAMPLE_DATA_OWNER, 
            username=username, division=DIVISION_NAME, category=POI_CATEGORY,
            attrs=", ".join(f"p.{a} AS {a}" for a in POI_ATTRS),
        ),
        client,
    )
    print(f"division: {division.iloc[0]['name']}  restaurants: {len(points)}")

    # Voronoi diagram is undefined for coincident input points (and would
    # produce duplicate cells with one cell per duplicate). Dedupe by
    # exact coordinates before passing to scipy; the points layer below
    # still keeps every original POI for inspection.
    coords_key = points.geometry.apply(lambda g: (g.x, g.y))
    points_for_voronoi = points[~coords_key.duplicated()].reset_index(drop=True)
    if len(points_for_voronoi) < len(points):
        print(
            f"deduped points for voronoi: {len(points)} -> "
            f"{len(points_for_voronoi)}"
        )

    cells = create_voronoi_with_attributes(
        points_for_voronoi,
        attribute_columns=POI_ATTRS,
        boundary=division.geometry.iloc[0],
    )
    cells["geometry"] = cells["geometry"].apply(_ensure_multipolygon)
    out = gpd.GeoDataFrame(
        cells[POI_ATTRS + ["geometry"]], crs=f"EPSG:{SRID}"
    )
    print(f"voronoi cells: {len(out)}")

    add_gdf_features_to_layer(
        client, out, target_layer,
        target_sr=SRID, geometry_type=TARGET_GEOMETRY, log=False,
    )

    points_out = gpd.GeoDataFrame(
        points[POI_ATTRS + ["geometry"]], crs=f"EPSG:{SRID}"
    )
    add_gdf_features_to_layer(
        client, points_out, points_layer,
        target_sr=SRID, geometry_type=POINTS_GEOMETRY, log=False,
    )
    print(f"\nwrote {len(out)} cells + {len(points_out)} source points")
