---
title: "Geoprocessing: buffers, union, validate"
---

# Geoprocessing: buffers, union, validate

Geoprocessing operations run on the server as background tasks: you
describe the source (an EQL query) and the target layer, the server
does the work and writes the result into a new layer. The helpers in
`evergis_tools.tasks.geoprocessing` wait for the task to finish and hand
you back the final status, so you do not poll anything by hand.

This recipe builds a few points, then draws a buffer around each of them
with `st_buffer` inside an EQL query. The same pattern - source EQL plus
target layer - is how union and geometry validation work too.

```python
import geopandas as gpd
from shapely.geometry import Point

from evergis_tools import Client
from evergis_tools.layers import gdf_to_layer
from evergis_tools.tasks.geoprocessing import copy_layer_via_eql

with Client() as client:
    username = client.account.get_user_info().username
    cookbook = f"{username}/Cookbook"

    # 1. Build a tiny source layer to work on (three points near Moscow).
    points = gpd.GeoDataFrame(
        {
            "name": ["a", "b", "c"],
            "geometry": [
                Point(37.61, 55.75),
                Point(37.62, 55.76),
                Point(37.60, 55.74),
            ],
        },
        crs="EPSG:4326",
    )
    source_layer = f"{username}.cookbook_points"
    gdf_to_layer(
        client=client,
        gdf=points,
        layer_name=source_layer,
        layer_alias="Cookbook points",
        geometry_type="Point",
        parent_path=cookbook,
        overwrite="cascade",  # safe to re-run: drops a previous copy first
    )

    # 2. Buffer each point by 0.01 degrees. The result is a polygon layer.
    #    st_buffer runs in the EQL; gid and geometry must stay named as the
    #    task expects (gid = id_attribute, geometry = geometry_attribute).
    buffer_layer = f"{username}.cookbook_buffers"
    eql = (
        "SELECT gid, name, st_buffer(geometry, 0.01) AS geometry "
        f"FROM {source_layer}"
    )
    result = copy_layer_via_eql(
        client=client,
        eql=eql,
        target_layer=buffer_layer,
        target_layer_alias="Cookbook buffers",
        target_layer_parent_path=cookbook,  # folder is created if missing
    )

    if result.is_successful:
        print(f"Buffer layer ready: {buffer_layer}")
    else:
        print(f"Buffer task did not finish cleanly: {result.status}")
        if result.error_message:
            print(f"  reason: {result.error_message}")
```

Notes:

- The source is always an **EQL query**, so you can filter and transform
  the geometry in one step. Here `st_buffer(geometry, 0.01)` produces the
  buffer; the layer is in EPSG:4326, so the radius is in degrees (about
  1.1 km at this latitude). For a buffer in metres, work in a projected
  layer instead.
- `gid` and `geometry` in the query keep their default names so the task
  can find the identifier and geometry columns. If you rename them, pass
  `source_id_attribute=` / `source_geometry_attribute=` to match.
- `target_layer_parent_path=` creates the `Cookbook` folder if it is not
  there yet, and the helper waits for the task before returning. Use
  `wait_for_completion=False` if you would rather start the task and check
  on it later.

Other geoprocessing helpers follow the same shape:

- `union_layers_via_eql(client, eql=..., target_layer=...)` merges the
  features from the query into one geometry (pass `group_attribute=` to
  union per group instead of all-into-one).
- `validate_layer_geometry(client, source_layer=..., target_layer=...)`
  writes any invalid geometries into the target layer with the reason in
  a column, so you can see what is broken before fixing it.
- `fix_layer_geometry(client, layer_name=...)` repairs invalid geometries
  in place, in the original layer.

## See also

- [[quickstart|Quick start]]
- [[layer-from-geodataframe|Create a layer from a GeoDataFrame]]
