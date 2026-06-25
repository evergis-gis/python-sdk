"""Add features (Point geometry + attributes) to an existing layer.

Appends 3 stations to the seed Point layer ``evg_stations``
provisioned by the ``features`` theme. Each added station carries
``code='ADD-N'`` so the example is safe to re-run: previous additions
are removed before the new ones are appended.

Run the seed once:

    .venv/bin/python -m evergis_tutorial_setup themes features

To restore the seed to its initial state:

    python -m evergis_tutorial_setup themes features --force
"""

from datetime import datetime

import geopandas as gpd
from shapely.geometry import Point

from evergis_tools import Client
from evergis_tools.features import (
    add_gdf_features_to_layer,
    delete_features_by_condition,
)


TARGET_LAYER_SHORT = "evg_stations"
SRID = 4326

# Marker that lets the example clean up its own additions on re-run.
ADD_MARKER = "ADD-"


STATIONS = [
    {"code": "ADD-1", "elevation_m": 132.0, "floors_visible": 4,
     "is_active": True, "installed_at": datetime(2026, 5, 10, 9, 0, 0),
     "sensor_meta": {"vendor": "Vaisala"},
     "lon": 37.6500, "lat": 55.7400},
    {"code": "ADD-2", "elevation_m": 165.5, "floors_visible": 7,
     "is_active": True, "installed_at": datetime(2026, 5, 10, 9, 5, 0),
     "sensor_meta": {"vendor": "Davis"},
     "lon": 37.6800, "lat": 55.7600},
    {"code": "ADD-3", "elevation_m": 119.0, "floors_visible": 2,
     "is_active": False, "installed_at": datetime(2026, 5, 10, 9, 10, 0),
     "sensor_meta": None,
     "lon": 37.5800, "lat": 55.7300},
]


with Client() as client:
    username = client.account.get_user_info().username
    target_layer = f"{username}.{TARGET_LAYER_SHORT}"

    delete_features_by_condition(
        client, target_layer,
        f"WHERE code LIKE '{ADD_MARKER}%'",
    )

    gdf = gpd.GeoDataFrame(
        [{**s, "geometry": Point(s.pop("lon"), s.pop("lat"))} for s in STATIONS],
        crs=f"EPSG:{SRID}",
    )

    add_gdf_features_to_layer(
        client=client, gdf=gdf, layer_name=target_layer,
        target_sr=SRID, geometry_type="Point", log=False,
    )
    print(f"appended {len(gdf)} features to {target_layer}")
