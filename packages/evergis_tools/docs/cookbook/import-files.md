---
title: Import a file into a layer
---

# Import a file into a layer

To turn a data file (CSV, GeoPackage, shapefile, ...) into an EverGIS
layer you go through three steps:

1. **Upload** the file into the catalog with `upload_file`.
2. **Read its schema** from the server with `get_<format>_data_schema_rest`
   so you know the field names and types the file has.
3. **Import** it into a new layer with `import_<format>_to_layer`.

The schema step matters because the importer needs to know which source
field maps to which target field, and what type each field should become.
The helper `build_attribute_mappings_from_schema` builds those two maps
straight from the schema response, so you do not hand-write them.

The recipe below is self-contained: it writes a tiny CSV to a temporary
file, uploads it under `{username}/Cookbook`, reads the schema, and
imports it into a Point layer using the `lon` / `lat` columns as
coordinates.

```python
import tempfile
from pathlib import Path

from evergis_tools import Client
from evergis_tools.catalog import upload_file
from evergis_tools.tasks.import_tools import (
    get_csv_data_schema_rest,
    import_csv_to_layer,
)

# A tiny CSV we can create on the spot, so this recipe needs no
# pre-existing file. In real use you would point at your own data file.
CSV_TEXT = (
    "name,lon,lat,population\n"
    "Moscow,37.6173,55.7558,12655000\n"
    "Saint Petersburg,30.3351,59.9343,5384000\n"
    "Novosibirsk,82.9204,55.0084,1620000\n"
)

with Client() as client:
    username = client.account.get_user_info().username
    cookbook = f"{username}/Cookbook"

    # 1. Upload the source file into the catalog.
    with tempfile.TemporaryDirectory() as tmp:
        local_csv = Path(tmp) / "cities.csv"
        local_csv.write_text(CSV_TEXT, encoding="utf-8")
        uploaded = upload_file(client, local_csv, parent_path=cookbook)
    source_file = uploaded.resourceId

    # 2. Read the schema. CSV reports every column as String, so we fix
    #    the numeric columns to real types before importing.
    schema = get_csv_data_schema_rest(
        client,
        source_file,
        column_delimiter=",",
        coord_source_fields=["lon", "lat"],
    )
    print("Columns the server sees:")
    for attr in schema["layers"][0]["attributesConfiguration"]["attributes"]:
        print(f"  {attr['attributeName']:12s} {attr['type']}")

    attribute_type_mapping = {
        "name": "String",
        "lon": "Double",
        "lat": "Double",
        "population": "Int32",
    }
    # Identity rename: keep the source column names as-is.
    attribute_mapping = {name: name for name in attribute_type_mapping}

    # 3. Import into a new Point layer. The folder is created if missing.
    result = import_csv_to_layer(
        client,
        source_file_name=source_file,
        source_coord_fields=["lon", "lat"],
        target_layer=f"{username}.cookbook_cities",
        target_layer_alias="Cookbook cities",
        target_layer_parent_path=cookbook,
        column_delimiter=",",
        attribute_mapping=attribute_mapping,
        attribute_type_mapping=attribute_type_mapping,
    )
    print(f"Import finished: {result.status}")
```

Notes:

- `upload_file` returns a catalog record; its `.resourceId` is what the
  schema and import calls take as `source_file_name`. You can also pass
  the file's path (`username/Cookbook/cities.csv`) - both work.
- `source_coord_fields=["lon", "lat"]` tells the importer to build point
  geometry from those two columns. Leave it out for a table without
  geometry, or set `is_wkt=True` and point `source_coord_fields` at a
  single WKT column for line / polygon data.
- `attribute_type_mapping` is the important one for CSV: the server reads
  everything as text, so without it numbers stay strings. Declare
  `Double`, `Int32`, `DateTime`, etc. for the columns that need it.
- `import_csv_to_layer` waits for the import task to finish by default and
  returns a result with a `.status`. Pass `wait_for_completion=False` to
  fire it off without blocking.

## GeoPackage and other formats

A GeoPackage (`.gpkg`) is a container that can hold several layers, so the
flow is the same but you loop over the layers inside the file. Upload the
`.gpkg`, then:

- `get_gpkg_data_schema_rest(client, source_file)` with no `layer_name`
  returns the container's list of layers.
- `get_gpkg_data_schema_rest(client, source_file, layer_name=name)`
  returns one layer's schema.
- `build_attribute_mappings_from_schema(schema, layer_name=name)` builds
  the two maps for you (GeoPackage already carries real types, so you do
  not need to fix them by hand the way CSV requires).
- `import_gpkg_to_layer(client, source_file_name=source_file,
  source_layer_name=name, target_layer=..., ...)` imports that one layer.

The same `get_*_data_schema_rest` / `import_*_to_layer` pair exists for
`xlsx`, `shapefile` (a zipped `.shp`), and `fgdb` (a zipped `.gdb`).

## See also

- [[quickstart|Quick start]]
- [[layer-from-geodataframe|Create a layer from a GeoDataFrame]]
