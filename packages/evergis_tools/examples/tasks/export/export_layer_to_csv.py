"""Export an EverGIS layer to a CSV file via the importExport task.

CSV has no native geometry. The wrapper writes coordinates into two
columns (``lon``, ``lat``) via ``coord_source_fields`` so the file
opens in spreadsheets without WKT decoding.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import delete_resource
from evergis_tools.tasks.export_tools import export_layer_to_csv


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")

SOURCE_LAYER_SHORT = "evg_overture_metro_stations"
TARGET_FILE_NAME = "evg_export_metro_stations.csv"


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    source = f"{SAMPLE_DATA_OWNER}.{SOURCE_LAYER_SHORT}"
    results_path = f"{username}/{PROJECT_PATH}/tasks/results"
    results_path = f"{username}/{PROJECT_PATH}"

    # Cleanup the previous export so the task re-creates the file from
    # scratch instead of failing on "already exists".
    delete_resource(client, f"{results_path}/{TARGET_FILE_NAME}", missing_ok=True)

    result = export_layer_to_csv(
        client=client,
        source_layer=source,
        target_file_name=TARGET_FILE_NAME,
        target_parent_path=results_path,
        column_delimiter=",",
        coord_source_fields=["lon", "lat"],
        spatial_reference=4326,
        log=True,
    )
    print(f"{TARGET_FILE_NAME}: {result.status}")
