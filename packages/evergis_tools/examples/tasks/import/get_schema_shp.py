"""Print the server-side schema (importExport/dataSchema) for a Shapefile zip.

Unlike CSV/XLSX, Shapefile schema carries real attribute types (read from
DBF + .prj/.cpg), so ``build_attribute_mappings_from_schema`` produces
ready-to-use ``attribute_mapping`` / ``attribute_type_mapping``.

Source files live in the shared sample-data catalog owned by
``SAMPLE_DATA_OWNER`` (default ``edu``).
"""

import json
import os

from evergis_tools import Client
from evergis_tools.tasks.import_tools import get_shapefile_data_schema_rest


client = Client()
username = client.account.get_user_info().username

SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")

RESOURCE_ID = (
    f"{SAMPLE_DATA_OWNER}/EverGIS Sample Data Catalog/Source files - raw archives"
    "/Source files - Shapefile/german_lands.zip"
)


schema = get_shapefile_data_schema_rest(
    client=client,
    resource_id=RESOURCE_ID,
)
print(json.dumps(schema, indent=2, ensure_ascii=False))
