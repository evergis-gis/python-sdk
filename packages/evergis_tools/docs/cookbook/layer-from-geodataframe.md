---
title: Create a layer from a GeoDataFrame
---

# Create a layer from a GeoDataFrame

A GeoDataFrame is the usual way data arrives in Python - from a file, a
query, or a calculation. This recipe takes one and publishes it as a new
point layer in your catalog, in two steps:

1. `gdf_to_layer(...)` creates the layer and its columns from the
   GeoDataFrame (it reads the pandas dtypes to pick attribute types).
2. `add_gdf_features_to_layer(...)` inserts the rows.

Here the GeoDataFrame is built in code (5 points around central Moscow)
so the script runs on its own, but the same two calls work for a
GeoDataFrame loaded with `gpd.read_file(...)`.

```python
from datetime import datetime

import geopandas as gpd
from shapely.geometry import Point

from evergis_tools import Client
from evergis_tools.layers import gdf_to_layer
from evergis_tools.features import add_gdf_features_to_layer

# Source coordinate system: WGS84 lon/lat.
SRID = 4326

# Five points of interest. Each column becomes a layer attribute, and its
# pandas dtype decides the type: text -> STRING, int -> INT32,
# float -> DOUBLE, bool -> BOOLEAN, datetime -> DATETIME.
POIS = [
    {"name": "Red Square",      "category": "landmark", "score": 5.0, "visits_year": 12_000_000, "is_open": True,  "added_at": datetime(2024, 1, 15), "lon": 37.6208, "lat": 55.7539},
    {"name": "Bolshoi Theatre", "category": "culture",  "score": 4.8, "visits_year":    900_000, "is_open": True,  "added_at": datetime(2024, 2, 10), "lon": 37.6184, "lat": 55.7600},
    {"name": "Gorky Park",      "category": "park",     "score": 4.6, "visits_year":  6_000_000, "is_open": True,  "added_at": datetime(2024, 3,  5), "lon": 37.6017, "lat": 55.7314},
    {"name": "VDNH",            "category": "park",     "score": 4.5, "visits_year":  5_000_000, "is_open": True,  "added_at": datetime(2024, 3, 28), "lon": 37.6325, "lat": 55.8266},
    {"name": "Tretyakov",       "category": "museum",   "score": 4.7, "visits_year":  1_700_000, "is_open": False, "added_at": datetime(2024, 4, 12), "lon": 37.6207, "lat": 55.7414},
]

with Client() as client:
    username = client.account.get_user_info().username
    layer_name = "cookbook_points"
    # gdf_to_layer adds the "username." prefix; that system name is what
    # the feature calls below address.
    system_name = f"{username}.{layer_name}"
    parent = f"{username}/Cookbook"

    gdf = gpd.GeoDataFrame(
        [
            {
                "name": p["name"],
                "category": p["category"],
                "score": p["score"],
                "visits_year": p["visits_year"],
                "is_open": p["is_open"],
                "added_at": p["added_at"],
                "geometry": Point(p["lon"], p["lat"]),
            }
            for p in POIS
        ],
        crs=f"EPSG:{SRID}",
    )

    # Step 1: create the empty layer with columns matching the GeoDataFrame.
    # parent_path creates the Cookbook folder if it is not there yet.
    gdf_to_layer(
        client,
        gdf,
        layer_name,
        geometry_type="Point",
        srid=SRID,
        parent_path=parent,
        layer_alias="points from a GeoDataFrame",
        overwrite=True,
    )

    # Step 2: insert the rows. target_sr is the coordinate system of the
    # GeoDataFrame so the server reads the geometry correctly.
    add_gdf_features_to_layer(
        client,
        gdf,
        layer_name=system_name,
        target_sr=SRID,
        geometry_type="Point",
    )

    print(f"Layer saved: {parent}/{layer_name} ({len(gdf)} features)")
```

Notes:

- `gdf_to_layer` only creates the schema, it does not load any rows. The
  two-step split lets you create the layer once and add rows in several
  batches.
- `overwrite=True` replaces a layer of the same name if you run the
  script again. Use `overwrite="cascade"` if the layer has dependent
  resources (maps, query layers) that should be removed too.
- `geometry_type` must match the geometry in the GeoDataFrame: `Point`,
  `LineString`, `Polygon`, `MultiPolygon`, and so on.
- `srid` (on `gdf_to_layer`) sets the layer's stored coordinate system;
  `target_sr` (on `add_gdf_features_to_layer`) tells the server which
  coordinate system the incoming geometry uses. Keep both at the SRID of
  your data.

## See also

- [[quickstart|Quick start]]
- [[catalog-basics|Find and manage resources]]
