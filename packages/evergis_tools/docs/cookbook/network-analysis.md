---
title: "Network analysis: isochrones, routes, OD-matrix"
---

# Network analysis: isochrones, routes, OD-matrix

The EverGIS routing engine answers three everyday network questions
straight from coordinates, with no catalog resources to create first:

- `build_isochrone` - "where can I reach within N minutes from here?"
  Returns a reachability polygon.
- `build_route` - "what is the path from A to B?" Returns a line.
- `build_od_matrix_rest` - "how long between every origin and every
  destination?" Returns a table, one row per (from, to) pair.

All three call the routing worker in-process and hand you back plain
shapely geometry or a pandas DataFrame - nothing is published to your
catalog.

```python
from evergis_tools import Client
from evergis_tools.geo_tools import (
    build_isochrone,
    build_route,
    build_od_matrix_rest,
)
from shapely.geometry import Point

# Three points in central Moscow, as (longitude, latitude).
# Coordinates are WGS84 (EPSG:4326), so pass sr_in=4326.
red_square = Point(37.6208, 55.7539)
gorky_park = Point(37.6017, 55.7299)
vdnkh = Point(37.6342, 55.8263)

with Client() as client:
    # 1. Isochrone: the area reachable on foot within 10 minutes.
    #    The defaults walk; sr_in=4326 tells the worker our coordinates
    #    are lon/lat, sr_out=4326 returns the polygon in lon/lat too.
    area = build_isochrone(
        client, red_square, duration=10, sr_in=4326, sr_out=4326
    )
    if area is None:
        raise SystemExit("routing worker returned no isochrone")
    print(f"10-min walking area: {area.geom_type}, {area.area:.6f} sq.deg")

    # 2. Route: the walking path from Red Square to Gorky Park.
    path = build_route(
        client, red_square, gorky_park, sr_in=4326, sr_out=4326
    )
    if path is None:
        raise SystemExit("routing worker returned no route")
    print(f"route: {path.geom_type}, length {path.length:.6f} deg")

    # 3. OD-matrix: car travel time in seconds from each origin to each
    #    destination. Input points may be shapely Points, (x, y) tuples,
    #    or a GeoDataFrame; coordinates are in epsg_code.
    origins = [red_square, gorky_park]
    destinations = [vdnkh, gorky_park]
    od = build_od_matrix_rest(
        client,
        origins,
        destinations,
        transport_type="car",
        epsg_code=4326,
        seconds=True,
    )
    # Columns: from, to, distance, transporttype, weightparameter.
    # "from" / "to" are the row indices of the input lists; "distance"
    # holds travel time in seconds when seconds=True.
    print("OD matrix (seconds):")
    print(od.pivot(index="from", columns="to", values="distance").to_string())
```

Notes:

- Coordinate systems are explicit. The isochrone and route functions
  default `sr_in` to 3857 (Web Mercator); since the points above are
  lon/lat, pass `sr_in=4326` (and `sr_out=4326` to get results back in
  lon/lat). `build_od_matrix_rest` takes a single `epsg_code` for both
  input and output.
- Each function returns `None` (isochrone, route) when the worker finds
  no usable geometry - check for it before using the result. Real
  request or parsing errors are raised, not swallowed.
- `build_od_matrix_rest` is the synchronous, in-process variant for
  small point sets - it returns a DataFrame and publishes nothing. For
  large matrices that should land as a catalog layer, use the task-based
  `build_od_matrix` in `evergis_tools.tasks.network` instead.
- Switch travel mode with `transport_type` ("car", "pedestrian", ...);
  the server decides which modes it supports. Set `seconds=False` to get
  distance in metres instead of time.

## See also

- [[quickstart|Quick start]]
