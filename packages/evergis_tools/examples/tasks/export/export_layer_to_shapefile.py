"""Export an EverGIS layer to a Shapefile (.zip) via the importExport task.

The Shapefile format is a multi-file container, so the wrapper writes
a single ``.zip`` archive that bundles the ``.shp / .shx / .dbf / .prj``
quartet. Geometry is stored natively, no coordinate mapping is needed.
"""

import os

from evergis_tools import Client
from evergis_tools.catalog import delete_resource
from evergis_tools.tasks.export_tools import export_layer_to_shapefile


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")

SOURCE_LAYER_SHORT = "evg_overture_metro_stations"
TARGET_FILE_NAME = "evg_export_metro_stations.zip"


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    source = f"{SAMPLE_DATA_OWNER}.{SOURCE_LAYER_SHORT}"
    results_path = f"{username}/{PROJECT_PATH}/tasks/results"

    delete_resource(client, f"{results_path}/{TARGET_FILE_NAME}", missing_ok=True)

    result = export_layer_to_shapefile(
        client=client,
        source_layer=source,
        target_file_name=TARGET_FILE_NAME,
        target_parent_path=results_path,
        # Shapefile DBF column names are limited to 10 chars - keep
        # short names where the source attribute happens to be longer.
        attribute_mapping={
            "gid": "gid",
            "name": "name",
            "category": "category",
            "brand": "brand",
            "address": "address",
            "country_code": "ccode",
            "region_addr": "region",
            "geom": "geom",
        },
        log=False,
    )
    print(f"{TARGET_FILE_NAME}: {result.status}")
