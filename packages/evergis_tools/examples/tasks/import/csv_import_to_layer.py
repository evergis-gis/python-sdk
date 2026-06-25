"""Import a CSV file into an EverGIS Point layer via importExport task.

Prerequisite: the source file lives in the shared sample-data catalog
owned by ``SAMPLE_DATA_OWNER`` (default ``edu``); the import target is
created under the caller's own account.
"""

import os

from evergis_tools import Client, ResourceNotFound
from evergis_tools.catalog import add_layer_to_map
from evergis_tools.catalog.resources import resolve_resource
from evergis_tools.tasks.import_tools import import_csv_to_layer


client = Client()
username = client.account.get_user_info().username

PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")
SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")

SOURCE_FILE = (
    f"{SAMPLE_DATA_OWNER}/EverGIS Sample Data Catalog/Source files - raw archives"
    "/Source files - CSV/earthquakes_history.csv"
)
RESULTS_PATH = f"{username}/{PROJECT_PATH}/tasks/results"

TARGET_LAYER = f"{username}.{RESOURCE_PREFIX}_csv_earthquakes"
TARGET_LAYER_ALIAS = "csv import - earthquakes"

# Source -> target column rename (only magType -> mag_type is non-identity).
ATTRIBUTE_MAPPING = {
    "mag": "mag",
    "place": "place",
    "time": "time",
    "updated": "updated",
    "tz": "tz",
    "url": "url",
    "detail": "detail",
    "felt": "felt",
    "cdi": "cdi",
    "mmi": "mmi",
    "alert": "alert",
    "status": "status",
    "tsunami": "tsunami",
    "sig": "sig",
    "net": "net",
    "code": "code",
    "ids": "ids",
    "sources": "sources",
    "types": "types",
    "nst": "nst",
    "dmin": "dmin",
    "rms": "rms",
    "gap": "gap",
    "magType": "mag_type",
    "type": "type",
    "title": "title",
    "id": "id",
    "lon": "lon",
    "lat": "lat",
    "depth_km": "depth_km",
}

# CSV schema returns every field as String - declare real types explicitly
# so numbers stay numeric and timestamps land as DateTime.
ATTRIBUTE_TYPE_MAPPING = {
    "mag": "Double",
    "place": "String",
    "time": "DateTime",
    "updated": "DateTime",
    "tz": "Int32",
    "url": "String",
    "detail": "String",
    "felt": "Int32",
    "cdi": "Double",
    "mmi": "Double",
    "alert": "String",
    "status": "String",
    "tsunami": "Int32",
    "sig": "Int32",
    "net": "String",
    "code": "String",
    "ids": "String",
    "sources": "String",
    "types": "String",
    "nst": "Int32",
    "dmin": "Double",
    "rms": "Double",
    "gap": "Double",
    "mag_type": "String",
    "type": "String",
    "title": "String",
    "id": "String",
    "lon": "Double",
    "lat": "Double",
    "depth_km": "Double",
}


# Cascade-drop the target layer if it exists - otherwise the server fails
# with "table already exist" on re-run.
try:
    existing = resolve_resource(client, TARGET_LAYER)
    client.catalog.delete_resource(resourceId=existing.resourceId, cascade=True)
    print(f"dropped existing {TARGET_LAYER}")
except ResourceNotFound:
    pass

result = import_csv_to_layer(
    client=client,
    source_file_name=SOURCE_FILE,
    source_coord_fields=["lon", "lat"],
    target_layer=TARGET_LAYER,
    target_layer_alias=TARGET_LAYER_ALIAS,
    target_layer_parent_path=RESULTS_PATH,
    column_delimiter=",",
    attribute_mapping=ATTRIBUTE_MAPPING,
    attribute_type_mapping=ATTRIBUTE_TYPE_MAPPING,
    log=False,
)
add_layer_to_map(
    client, f"{username}.{RESOURCE_PREFIX}_map_tasks", TARGET_LAYER,
)
print(f"{TARGET_LAYER}: {result.status}")
