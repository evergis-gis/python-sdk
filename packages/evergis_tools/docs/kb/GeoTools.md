---
title: GeoTools
module: evergis_tools.geo_tools
---

# GeoTools

Network analysis and spatial utilities. Import: `from evergis_tools.geo_tools.network import ...`

## build_isochrone
Build isochrone (accessibility area) via EverGIS Worker API.

```python
from evergis_tools.geo_tools.network import build_isochrone
from shapely.geometry import Point

polygon = build_isochrone(
    client, Point(37.6, 55.7),
    duration=600,  # seconds
    provider_name="sproute_isochrone_pedestrian",
    sr_in=4326, sr_out=4326,
)
# Returns: Polygon or MultiPolygon; None when the worker returns no geometry; raises on request errors
```

**Providers:** `sproute_isochrone_pedestrian`, `sproute_isochrone_car`

## build_route
Build route between two points.

```python
from evergis_tools.geo_tools.network import build_route

line = build_route(
    client, Point(37.6, 55.7), Point(37.7, 55.8),
    provider_name="sproute_route_pedestrian",
    sr_in=4326, sr_out=4326,
)
# Returns: LineString or MultiLineString; None when the response has no route; raises on request errors
```

**Providers:** `sproute_route_pedestrian`, `sproute_route_car`

## build_od_matrix_rest
Synchronously compute an origin-destination matrix via the worker REST API (`POST /scheduler/worker` with `workerType=netEngine`, `methodType=ODMatrix-rest`). One row per (from, to) pair.

```python
from evergis_tools.geo_tools.network import build_od_matrix_rest
from shapely.geometry import Point

df = build_od_matrix_rest(
    client,
    points_from=[Point(37.6, 55.7), Point(37.7, 55.8)],
    points_to=[Point(37.5, 55.6)],
    transport_type="car",
    epsg_code=4326,
    seconds=True,
)
```

**Params:**

| Param | Default | Description |
|-------|---------|-------------|
| `client` | required | EverGIS API client |
| `points_from` | required | Origin points: `GeoDataFrame`, list of shapely `Point`, or list of `(x, y)` tuples. Coordinates in `epsg_code` |
| `points_to` | required | Destination points; same accepted types as `points_from` |
| `transport_type` | `"car"` | Transport mode (`"car"`, `"pedestrian"`, ...). Keyword-only |
| `epsg_code` | `4326` | SRID of the input coordinates (`3857` also works). Keyword-only |
| `seconds` | `True` | `True` returns travel time in seconds, `False` returns distance in metres. Keyword-only |
| `log` | `False` | If `True`, log info messages. Keyword-only |

**Returns:** `pandas.DataFrame` with columns `from, to, distance, transporttype, weightparameter` - one row per ordered pair (`len(points_from)` x `len(points_to)`).

> **Note:** Raises `ValueError` if either point set is empty, and `RuntimeError` if the worker response is not a dict with a `features` key.

> **Note:** This is the synchronous N x M variant - it returns a DataFrame in-process and publishes no result layer. For the task-based variant that writes an output layer, use [[Tasks/Network|build_od_matrix]] from `evergis_tools.tasks.network`.

## Voronoi (geo_tools.voronoi)

```python
from evergis_tools.geo_tools.voronoi import create_voronoi_cells, create_voronoi_with_attributes

cells = create_voronoi_cells(points_gdf, boundary_gdf)
cells_with_attrs = create_voronoi_with_attributes(points_gdf, boundary_gdf)
```

## See Also
- [[Tasks]] - Batch isochrones/routes via task system
