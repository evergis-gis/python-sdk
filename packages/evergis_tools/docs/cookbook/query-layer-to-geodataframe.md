---
title: Query a layer into a GeoDataFrame
---

# Query a layer into a GeoDataFrame

`query_layer_to_gdf` reads features from a layer and hands you back a
`geopandas.GeoDataFrame` with its geometry column decoded and its CRS
set, so you can filter, plot or join right away. You can narrow the read
with `conditions` (SQL `WHERE` fragments) and keep filter values out of
the query string by passing them as `@`-parameters.

This recipe is self-contained: it first builds a tiny point layer under
your `Cookbook` folder, then queries it back two ways.

```python
import geopandas as gpd
from shapely.geometry import Point

from evergis_tools import Client
from evergis_tools.layers import gdf_to_layer
from evergis_tools.features import add_gdf_features_to_layer, query_layer_to_gdf

with Client() as client:
    username = client.account.get_user_info().username
    # System name = {username}.{name}, unique across the catalog. Feature
    # and query calls address the layer by this, not by folder path.
    system_name = f"{username}.cookbook_cities"

    # Build a small GeoDataFrame to act on.
    cities = gpd.GeoDataFrame(
        {
            "name": ["Moscow", "Kazan", "Sochi", "Omsk"],
            "population": [13_100_000, 1_300_000, 466_000, 1_100_000],
            "geometry": [
                Point(37.6173, 55.7558),
                Point(49.1064, 55.7963),
                Point(39.7303, 43.6028),
                Point(73.3686, 54.9893),
            ],
        },
        crs="EPSG:4326",
    )

    # Create the layer (schema only) under the Cookbook folder, then load
    # the rows. overwrite="cascade" makes the script safe to re-run.
    gdf_to_layer(
        client,
        cities,
        "cookbook_cities",
        geometry_type="Point",
        parent_path=f"{username}/Cookbook",
        overwrite="cascade",
    )
    add_gdf_features_to_layer(
        client, cities, layer_name=system_name,
        target_sr=4326, geometry_type="Point",
    )

    # 1. Read everything back, sorted by population (descending).
    #    "-population" means DESC; "population" would be ASC.
    everything = query_layer_to_gdf(
        client,
        layer_name=system_name,
        attributes=["name", "population", "geometry"],
        sort=["-population"],
    )
    print(f"all rows: {len(everything)}  crs: {everything.crs}")
    print(everything.drop(columns="geometry").to_string(index=False))

    # 2. Read a filtered subset. The filter value lives in parameters,
    #    not in the WHERE string, so it is passed safely to the server.
    big_cities = query_layer_to_gdf(
        client,
        layer_name=system_name,
        attributes=["name", "population", "geometry"],
        conditions=["WHERE population >= @min_pop"],
        parameters={"@min_pop": 1_000_000},
        sort=["-population"],
    )
    print(f"\ncities over 1M: {len(big_cities)}")
    for _, row in big_cities.iterrows():
        print(f"  {row['name']:8s} {row['population']:>10,}  {row.geometry.wkt}")
```

Notes:

- Pass either `layer_name` (the system name `username.cookbook_cities`,
  unique across the catalog) or `layer_path` (the resource path
  `username/Folder/<alias>`, using the layer alias, not the system name) -
  not both. Here we use `layer_name`.
- `attributes` is the list of columns to fetch. Include `"geometry"` to
  get the shapes back; if you leave `attributes` out entirely you get all
  columns.
- `conditions` is a list of SQL `WHERE` fragments. Keep concrete values
  out of them: write `@min_pop` in the condition and supply the value in
  `parameters`. The same `@`-parameter can be reused if the layer itself
  declares EQL parameters.
- `sort` uses the `±field` form: `"population"` is ascending, `"-population"`
  is descending. The SQL `"population DESC"` form is not accepted.
- The returned object is a real `GeoDataFrame`, so `everything.plot()`,
  `.to_file(...)` and spatial joins all work.

## See also

- [[layer-from-geodataframe|Create a layer from a GeoDataFrame]]
- [[quickstart|Quick start]]
