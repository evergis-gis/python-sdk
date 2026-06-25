"""Export an EverGIS layer to an XLSX file via the importExport task.

Same pattern as the CSV export - XLSX has no native geometry, so
coordinates are emitted into two columns (``lon``, ``lat``) via
``coord_source_fields``.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import delete_resource
from evergis_tools.tasks.export_tools import export_layer_to_xlsx


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")

SOURCE_LAYER_SHORT = "evg_overture_metro_stations"
TARGET_FILE_NAME = "evg_export_metro_stations.xlsx"


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    source = f"{SAMPLE_DATA_OWNER}.{SOURCE_LAYER_SHORT}"
    results_path = f"{username}/{PROJECT_PATH}/tasks/results"

    delete_resource(client, f"{results_path}/{TARGET_FILE_NAME}", missing_ok=True)

    result = export_layer_to_xlsx(
        client=client,
        source_layer=source,
        target_file_name=TARGET_FILE_NAME,
        target_parent_path=results_path,
        coord_source_fields=["lon", "lat"],
        spatial_reference=4326,
        log=False,
    )
    print(f"{TARGET_FILE_NAME}: {result.status}")
