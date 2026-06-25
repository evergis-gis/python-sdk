---
title: Add, edit and delete features
---

# Add, edit and delete features

Once a layer exists, you keep its rows up to date by adding new
features, editing the ones already there, and deleting the ones you no
longer want. This recipe does all three on a point layer it builds from
scratch, printing the feature count between steps so each change is
visible.

The three workhorse functions:

- `add_gdf_features_to_layer` - append rows from a GeoDataFrame.
- `edit_layer_by_gdf` - change attribute (and geometry) values of
  existing rows, matched by an id column.
- `delete_features_by_condition` - drop every row matching an EQL
  `WHERE` clause.

`count_features` reports the number of rows; pass a `condition` (the
WHERE body, without the leading `WHERE`) to count just a subset.

```python
import geopandas as gpd
from shapely.geometry import Point

from evergis_tools import Client
from evergis_tools.layers import gdf_to_layer
from evergis_tools.features import (
    add_gdf_features_to_layer,
    edit_layer_by_gdf,
    delete_features_by_condition,
    count_features,
)

with Client() as client:
    username = client.account.get_user_info().username
    layer_name = "cookbook_stations"
    # gdf_to_layer adds the "username." prefix, so the system name we use
    # for the feature calls below is predictable.
    system_name = f"{username}.{layer_name}"

    # Create an empty point layer. The schema (status text, load number)
    # is taken from the columns of this GeoDataFrame. parent_path creates
    # the Cookbook folder for you if it is not there yet.
    seed = gpd.GeoDataFrame(
        {"status": ["open"], "load": [10]},
        geometry=[Point(37.6, 55.75)],
        crs="EPSG:4326",
    )
    gdf_to_layer(
        client=client,
        gdf=seed,
        layer_name=layer_name,
        parent_path=f"{username}/Cookbook",
        overwrite="cascade",  # safe to re-run: drop an old copy first
        geometry_type="Point",
        log=False,
    )

    # 1. Add three stations.
    new_stations = gpd.GeoDataFrame(
        {"status": ["open", "closed", "open"], "load": [42, 0, 17]},
        geometry=[Point(37.61, 55.76), Point(37.62, 55.74), Point(37.59, 55.77)],
        crs="EPSG:4326",
    )
    add_gdf_features_to_layer(
        client=client, gdf=new_stations, layer_name=system_name,
        target_sr=4326,  # match the layer's coordinate system
        log=False,
    )
    print(f"after add:    {count_features(client, system_name)} stations")

    # 2. Edit two of the open stations. edit_layer_by_gdf matches rows by
    #    the "id" column - here the server-assigned gid values 1 and 3
    #    (the layer started empty, so the three added rows got gid 1-3).
    #    Only the listed columns change, but geometry must be supplied.
    edits = gpd.GeoDataFrame(
        {"id": [1, 3], "status": ["maintenance", "open"], "load": [5, 99]},
        geometry=[Point(37.61, 55.76), Point(37.59, 55.77)],
        crs="EPSG:4326",
    )
    edit_layer_by_gdf(
        client=client, gdf=edits, layer_name=system_name,
        id_column="id", target_sr=4326, log=False,
    )

    # 3. Delete every closed station. Both calls take an EQL filter;
    #    include the WHERE keyword (count_features also accepts it without
    #    and adds it for you).
    closed = count_features(client, system_name, condition="WHERE status = 'closed'")
    delete_features_by_condition(
        client, system_name, "WHERE status = 'closed'",
    )
    print(f"deleted {closed} closed station(s)")
    print(f"after delete: {count_features(client, system_name)} stations")
```

Notes:

- `gdf_to_layer` infers the layer schema from the GeoDataFrame columns,
  so the layer you create here already has a `status` text field and a
  `load` number field. The server assigns each row an integer `gid`
  starting at 1.
- `add_gdf_features_to_layer` needs the layer **system name**
  (`username.layer_name`), not the catalog path. We build it from the
  name we passed to `gdf_to_layer`.
- `edit_layer_by_gdf` matches rows by the column named in `id_column`
  and needs the geometry of each edited row, even when you only mean to
  change attributes. To edit attributes of a table without geometry, use
  `edit_layer_by_df` instead.
- `count_features` takes the WHERE body alone (`status = 'closed'`),
  while `delete_features_by_condition` expects the full clause including
  the leading `WHERE`. That mismatch is the EverGIS convention, so it is
  worth keeping in mind.
- For filtering on a value that comes from user input, read it with the
  parameter-aware reader `query_layer_to_gdf(..., conditions=["WHERE
  status = @s"], parameters={"@s": value})` rather than building the
  string by hand.

## See also

- [[layer-from-geodataframe|Create a layer from a GeoDataFrame]]
- [[quickstart|Quick start]]
