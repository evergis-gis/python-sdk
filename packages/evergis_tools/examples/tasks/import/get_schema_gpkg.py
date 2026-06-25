"""Print the server-side schema (importExport/dataSchema) for a GPKG file.

GPKG is a multi-layer container. The endpoint has two modes:

* without ``layer_name`` - returns the container's table of contents;
* with ``layer_name`` - returns one layer's schema, ready for
  ``build_attribute_mappings_from_schema``.

This example calls both on the same file.

Source files live in the shared sample-data catalog owned by
``SAMPLE_DATA_OWNER`` (default ``edu``).
"""

import json
import os

from evergis_tools import Client
from evergis_tools.tasks.import_tools import get_gpkg_data_schema_rest


client = Client()
username = client.account.get_user_info().username

SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")

RESOURCE_ID = (
    f"{SAMPLE_DATA_OWNER}/EverGIS Sample Data Catalog/Source files - raw archives"
    "/Source files - GeoPackage gpkg/natural_earth_110m.gpkg"
)


# A call without layer_name returns the list of every layer in the file.
toc = get_gpkg_data_schema_rest(client, RESOURCE_ID)
print("=== layers in container ===")
print(json.dumps(toc, indent=2, ensure_ascii=False))

# First layer's full schema (fields + types).
first_layer_name = toc["layers"][0]["name"]
schema = get_gpkg_data_schema_rest(client, RESOURCE_ID, layer_name=first_layer_name)
print(f"\n=== layer schema: {first_layer_name} ===")
print(json.dumps(schema, indent=2, ensure_ascii=False))
