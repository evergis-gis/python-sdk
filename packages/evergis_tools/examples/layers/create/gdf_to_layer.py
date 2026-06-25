"""Create an EverGIS layer from a GeoDataFrame.

Builds a small synthetic GeoDataFrame in code (5 POIs around central
Moscow) and publishes it as a new ``Point`` layer at
``{PROJECT_PATH}/layers/results/<username>.evg_gdf_demo``.

Demonstrates the most common pattern: take a GeoDataFrame from anywhere
(file, query, calculation), call ``gdf_to_layer`` to publish the schema,
then ``add_gdf_features_to_layer`` to insert the rows.

The ``POIS`` records cover every pandas dtype the wrapper auto-detects:

    pandas dtype          ->  AttributeType
    ---------------------     --------------
    object / str          ->  STRING
    integer               ->  INT32
    float                 ->  DOUBLE
    bool                  ->  BOOLEAN
    datetime64            ->  DATETIME

(Anything else falls back to STRING. For Pydantic-driven schemas with
INT64 / JSON, see ``create_layer_from_schema_with_geometry.py``.)
"""

import os
from datetime import datetime

import geopandas as gpd
from shapely.geometry import Point

from evergis_tools import Client
from evergis_tools.catalog import add_layer_to_map, delete_resource
from evergis_tools.features import add_gdf_features_to_layer
from evergis_tools.layers import gdf_to_layer


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")

LAYER_SHORT = "gdf_demo"
LAYER_ALIAS = "synthetic POIs around Moscow"
GEOMETRY_TYPE = "Point"
SRID = 4326

POIS = [
    {"name": "Red Square",      "category": "landmark", "score": 5.0, "visits_year": 12_000_000, "is_open": True,  "added_at": datetime(2024, 1, 15), "lon": 37.6208, "lat": 55.7539},
    {"name": "Bolshoi Theatre", "category": "culture",  "score": 4.8, "visits_year":    900_000, "is_open": True,  "added_at": datetime(2024, 2, 10), "lon": 37.6184, "lat": 55.7600},
    {"name": "Gorky Park",      "category": "park",     "score": 4.6, "visits_year":  6_000_000, "is_open": True,  "added_at": datetime(2024, 3,  5), "lon": 37.6017, "lat": 55.7314},
    {"name": "VDNH",            "category": "park",     "score": 4.5, "visits_year":  5_000_000, "is_open": True,  "added_at": datetime(2024, 3, 28), "lon": 37.6325, "lat": 55.8266},
    {"name": "Tretyakov",       "category": "museum",   "score": 4.7, "visits_year":  1_700_000, "is_open": False, "added_at": datetime(2024, 4, 12), "lon": 37.6207, "lat": 55.7414},
]


with Client() as client:
    username = client.account.get_user_info().username
    target_layer = f"{username}.{RESOURCE_PREFIX}_{LAYER_SHORT}"
    target_parent = f"{username}/{PROJECT_PATH}/layers/results"

    delete_resource(client, target_layer, missing_ok=True)

    gdf = gpd.GeoDataFrame(
        [
            {
                "name": p["name"],            # STRING
                "category": p["category"],    # STRING
                "score": p["score"],          # DOUBLE
                "visits_year": p["visits_year"],  # INT32
                "is_open": p["is_open"],      # BOOLEAN
                "added_at": p["added_at"],    # DATETIME
                "geometry": Point(p["lon"], p["lat"]),
            }
            for p in POIS
        ],
        crs=f"EPSG:{SRID}",
    )

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
    print(f"layer saved: {target_parent}/{target_layer}  ({len(gdf)} features)")
