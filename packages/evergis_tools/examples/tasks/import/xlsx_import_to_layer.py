"""Import an XLSX file into an EverGIS Point layer via importExport task.

Shows how to specify XLSX-only parameters: ``attribute_name_row_number``
and ``first_data_row_number`` for sheets where headers are not on row 1.

Prerequisite: the source file lives in the shared sample-data catalog
owned by ``SAMPLE_DATA_OWNER`` (default ``edu``); the import target is
created under the caller's own account.
"""

import os

from evergis_tools import Client, ResourceNotFound
from evergis_tools.catalog import add_layer_to_map
from evergis_tools.catalog.resources import resolve_resource
from evergis_tools.tasks.import_tools import import_xlsx_to_layer


client = Client()
username = client.account.get_user_info().username

PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")
SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")

SOURCE_FILE = (
    f"{SAMPLE_DATA_OWNER}/EverGIS Sample Data Catalog/Source files - raw archives"
    "/Source files - Excel xlsx/chicago_crimes.xlsx"
)
RESULTS_PATH = f"{username}/{PROJECT_PATH}/tasks/results"

TARGET_LAYER = f"{username}.{RESOURCE_PREFIX}_xlsx_chicago_crimes"
TARGET_LAYER_ALIAS = "xlsx import - chicago_crimes"

# Source -> target column rename (identity map; included for completeness).
ATTRIBUTE_MAPPING = {
    "id": "id",
    "case_number": "case_number",
    "date": "date",
    "block": "block",
    "iucr": "iucr",
    "primary_type": "primary_type",
    "description": "description",
    "location_description": "location_description",
    "arrest": "arrest",
    "domestic": "domestic",
    "beat": "beat",
    "district": "district",
    "ward": "ward",
    "community_area": "community_area",
    "fbi_code": "fbi_code",
    "x_coordinate": "x_coordinate",
    "y_coordinate": "y_coordinate",
    "year": "year",
    "updated_on": "updated_on",
    "latitude": "latitude",
    "longitude": "longitude",
}

# XLSX schema returns every field as String - declare real types explicitly
# so numerics, dates and booleans land correctly.
ATTRIBUTE_TYPE_MAPPING = {
    "id": "Int32",
    "case_number": "String",
    "date": "DateTime",
    "block": "String",
    "iucr": "String",
    "primary_type": "String",
    "description": "String",
    "location_description": "String",
    "arrest": "Boolean",
    "domestic": "Boolean",
    "beat": "Int32",
    "district": "Int32",
    "ward": "Int32",
    "community_area": "Int32",
    "fbi_code": "String",
    "x_coordinate": "Double",
    "y_coordinate": "Double",
    "year": "Int32",
    "updated_on": "DateTime",
    "latitude": "Double",
    "longitude": "Double",
}


# Cascade-drop the target layer if it exists - otherwise the server fails
# with "table already exist" on re-run.
try:
    existing = resolve_resource(client, TARGET_LAYER)
    client.catalog.delete_resource(resourceId=existing.resourceId, cascade=True)
    print(f"dropped existing {TARGET_LAYER}")
except ResourceNotFound:
    pass

# Headers on Excel row 1, data from row 2; no separate aliases row.
result = import_xlsx_to_layer(
    client=client,
    source_file_name=SOURCE_FILE,
    source_coord_fields=["longitude", "latitude"],
    target_layer=TARGET_LAYER,
    target_layer_alias=TARGET_LAYER_ALIAS,
    target_layer_parent_path=RESULTS_PATH,
    attribute_name_row_number=1,
    first_data_row_number=2,
    attribute_mapping=ATTRIBUTE_MAPPING,
    attribute_type_mapping=ATTRIBUTE_TYPE_MAPPING,
    spatial_reference=4326,
    log=False,
)
add_layer_to_map(
    client, f"{username}.{RESOURCE_PREFIX}_map_tasks", TARGET_LAYER,
)
print(f"{TARGET_LAYER}: {result.status}")
