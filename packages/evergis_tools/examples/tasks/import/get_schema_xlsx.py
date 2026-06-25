"""Print the server-side schema (importExport/dataSchema) for an XLSX file.

``attribute_name_row_number`` / ``first_data_row_number`` tell the server
where headers and data start in the sheet (1-based). XLSX schema also
comes back as String - declare real types explicitly in the import script.

Source files live in the shared sample-data catalog owned by
``SAMPLE_DATA_OWNER`` (default ``edu``).
"""

import json
import os

from evergis_tools import Client
from evergis_tools.tasks.import_tools import get_xlsx_data_schema_rest


client = Client()
username = client.account.get_user_info().username

SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")

RESOURCE_ID = (
    f"{SAMPLE_DATA_OWNER}/EverGIS Sample Data Catalog/Source files - raw archives"
    "/Source files - Excel xlsx/chicago_crimes.xlsx"
)


schema = get_xlsx_data_schema_rest(
    client=client,
    resource_id=RESOURCE_ID,
    attribute_name_row_number=1,
    first_data_row_number=2,
)
print(json.dumps(schema, indent=2, ensure_ascii=False))
