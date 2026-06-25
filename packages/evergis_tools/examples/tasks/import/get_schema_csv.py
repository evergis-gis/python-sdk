"""Print the server-side schema (importExport/dataSchema) for a CSV file.

Useful before an import: ``build_attribute_mappings_from_schema`` derives
``attribute_mapping`` / ``attribute_type_mapping`` from this response.
Note: for CSV every field comes back as String - declare real types
explicitly in the import script.

Source files live in the shared sample-data catalog owned by
``SAMPLE_DATA_OWNER`` (default ``edu``).
"""

import json
import os

from evergis_tools import Client
from evergis_tools.tasks.import_tools import get_csv_data_schema_rest


client = Client()
username = client.account.get_user_info().username

SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")

RESOURCE_ID = (
    f"{SAMPLE_DATA_OWNER}/EverGIS Sample Data Catalog/Source files - raw archives"
    "/Source files - CSV/earthquakes_history.csv"
)


schema = get_csv_data_schema_rest(
    client=client,
    resource_id=RESOURCE_ID,
    column_delimiter=",",
)
print(json.dumps(schema, indent=2, ensure_ascii=False))
