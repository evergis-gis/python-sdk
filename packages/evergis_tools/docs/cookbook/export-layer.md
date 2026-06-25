---
title: Export a layer to a file
---

# Export a layer to a file

This recipe takes a layer in your catalog and writes it out as a file -
a GeoPackage (`.gpkg`, keeps the geometry) and a CSV (a flat table with
two coordinate columns). It then downloads both files to your local
disk so you can open them in QGIS, a spreadsheet, or share them.

To stay self-contained, the script first creates a tiny three-point
layer under `Cookbook` and exports that. Swap `source_layer` for any
layer you already own to export your own data.

```python
from evergis_tools import Client, create_export_mappings_from_layer, gdf_to_layer
from evergis_tools.catalog import delete_resource, download_file, iter_resources
from evergis_tools.tasks.export_tools import export_layer_to_csv, export_layer_to_gpkg

import geopandas as gpd
from shapely.geometry import Point

with Client() as client:
    username = client.account.get_user_info().username
    folder = f"{username}/Cookbook"

    # Build a small sample layer so this recipe runs on its own.
    # Replace this with a layer you already have to export your data.
    gdf = gpd.GeoDataFrame(
        {
            "name": ["Office", "Warehouse", "Shop"],
            "geometry": [Point(37.62, 55.75), Point(37.50, 55.70), Point(37.70, 55.80)],
        },
        crs="EPSG:4326",
    )
    gdf_to_layer(
        client=client,
        gdf=gdf,
        layer_name="cookbook_export_src",
        parent_path=folder,
        geometry_type="Point",
        overwrite="cascade",  # safe to re-run: drops the layer if it is already there
    )
    source_layer = f"{username}.cookbook_export_src"

    # Export to GeoPackage. The server-side gpkg handler needs the field
    # name and type maps; this helper reads them straight off the layer.
    attr_map, type_map = create_export_mappings_from_layer(
        client, source_layer, log=False,
    )
    gpkg_result = export_layer_to_gpkg(
        client=client,
        source_layer=source_layer,
        target_file_name="cookbook_points.gpkg",
        target_parent_path=folder,
        attribute_mapping=attr_map,
        attribute_type_mapping=type_map,
    )
    print(f"GeoPackage export: {gpkg_result.status}")

    # Export to CSV. CSV has no geometry column, so the coordinates are
    # written into two plain columns named "lon" and "lat".
    csv_result = export_layer_to_csv(
        client=client,
        source_layer=source_layer,
        target_file_name="cookbook_points.csv",
        target_parent_path=folder,
        column_delimiter=",",
        coord_source_fields=["lon", "lat"],
        spatial_reference=4326,
    )
    print(f"CSV export: {csv_result.status}")

    # The export task currently appends a timestamp to the file name and
    # places the result in your root folder (not target_parent_path), so
    # find the produced File by name prefix rather than by a fixed path.
    def fetch_export(prefix: str) -> str:
        files = [
            r for r in iter_resources(client, filter_text=f"{prefix}*", owner_filter="My")
            if r.type == "File"
        ]
        if not files:
            raise RuntimeError(f"exported file {prefix!r} not found")
        newest = max(files, key=lambda r: r.name)  # timestamp suffix sorts newest last
        local = download_file(client, newest.resourceId, "/tmp/", overwrite=True)
        delete_resource(client, newest.resourceId, missing_ok=True)  # drop the server copy
        return local

    print(f"Saved {fetch_export('cookbook_points.gpkg')}")
    print(f"Saved {fetch_export('cookbook_points.csv')}")
```

Notes:

- `export_layer_to_gpkg` and `export_layer_to_csv` run a server-side
  task and, by default, wait for it to finish before returning. The
  returned object has a `.status` you can print.
- The output file is created at `target_parent_path/target_file_name`.
  Pass the file name in `target_file_name` and the folder in
  `target_parent_path`; the folder is created if it does not exist.
- `create_export_mappings_from_layer` builds the field-name and
  field-type maps the GeoPackage handler needs. CSV does not require
  them, so the CSV call leaves them out.
- `download_file` saves into a folder when the target ends with `/`
  (the file keeps its catalog name), or to an exact path otherwise.
  `overwrite=True` lets you re-run without a "file exists" error.
- To export only part of a layer, pass `source_layer_condition="..."`
  (a WHERE clause) or a full `source_eql` query with `@`-parameters.

## See also

- [[layer-from-geodataframe|Create a layer from a GeoDataFrame]]
- [[import-file-to-layer|Import a file into a layer]]
</content>
</invoke>
