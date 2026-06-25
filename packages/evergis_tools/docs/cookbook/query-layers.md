---
title: Build a query (virtual) layer with EQL
---

# Build a query (virtual) layer with EQL

A query layer (also called a virtual layer) is a layer whose contents are
defined by an EQL query instead of its own stored table. It always shows
the current result of that query over other layers - filter rows, join
tables, or compute new columns, without copying any data.

This recipe is self-contained: it first creates a small base layer of
points under `{username}/Cookbook`, then builds a query layer that selects
a filtered subset of those points. The filter value is passed as an
`@`-parameter, so the same query template works for any category without
gluing user input into the SQL text.

```python
from evergis_tools import Client
from evergis_tools.layers import gdf_to_layer, create_query_layer
import geopandas as gpd
from shapely.geometry import Point

with Client() as client:
    username = client.account.get_user_info().username
    folder = f"{username}/Cookbook"

    # 1. Create a small base layer to query against. In your own work this
    #    is usually an existing layer - here we make one so the recipe runs
    #    on its own.
    base_layer = f"{username}.cookbook_places"
    gdf = gpd.GeoDataFrame(
        {
            "name": ["Cafe", "Pharmacy", "Bakery", "Clinic"],
            "category": ["food", "health", "food", "health"],
            "geometry": [
                Point(37.62, 55.75),
                Point(37.63, 55.76),
                Point(37.61, 55.74),
                Point(37.64, 55.77),
            ],
        },
        crs="EPSG:4326",
    )
    gdf_to_layer(
        client=client,
        gdf=gdf,
        layer_name=base_layer,
        layer_alias="Cookbook places",
        parent_path=folder,
        geometry_type="Point",
        overwrite=True,
    )

    # 2. Build a query layer over the base layer. The EQL keeps only rows
    #    matching @category. Change CATEGORY and re-run to filter differently
    #    without touching the query text.
    CATEGORY = "food"
    query = f"SELECT gid, name, category, geometry FROM {base_layer} WHERE category = @category"

    create_query_layer(
        client=client,
        layer_name=f"{username}.cookbook_food_places",
        eql_query=query,
        eql_parameters={"@category": CATEGORY},
        layer_alias="Food places (query layer)",
        parent_path=folder,
        geometry_type="Point",
        overwrite=True,
    )

    print(f"Query layer created under {folder} (category = {CATEGORY})")
```

Notes:

- `create_query_layer` defaults to `create_table=False`, so the result is
  a true virtual layer - no second copy of the data. Pass
  `create_table=True` if you want the query result stored as its own
  physical table (useful when the underlying data rarely changes and you
  want fast reads).
- The EQL refers to the base layer by its table name (`username.name`),
  which is the layer's system name - the same value you passed as
  `layer_name`, not the catalog folder path.
- `eql_parameters` takes plain Python values; the type (here a string) is
  detected automatically. Always pass filter values this way instead of
  building the query string from user input.
- `geometry_type` tells the layer how to render its rows on a map. Use the
  geometry type the query returns (`Point`, `LineString`, `Polygon`,
  `MultiPolygon`, ...).
- Pass `client_style=<Mapbox GL style dict>` to `create_query_layer` to
  color the layer the moment it appears on a map.

## See also

- [[quickstart|Quick start]]
- [[layer-from-geodataframe|Create a layer from a GeoDataFrame]]
