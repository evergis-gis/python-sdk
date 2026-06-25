"""Export an EverGIS layer to a GeoJSON file via the importExport task.

The server-side ``layer → geojson`` handler crashes with a null-reference
exception unless both ``attributeMapping`` and ``attributeTypeMapping``
are provided in the request. ``create_export_mappings_from_layer``
reads the layer schema and builds both maps with identity field names
and the EverGIS-native types so we don't hand-write them per example.
"""

import os

from evergis_tools import Client, create_export_mappings_from_layer
from evergis_tools.catalog import delete_resource
from evergis_tools.tasks.export_tools import export_layer_to_geojson


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")

SOURCE_LAYER_SHORT = "evg_overture_metro_stations"
TARGET_FILE_NAME = "evg_export_metro_stations.geojson"


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    source = f"{SAMPLE_DATA_OWNER}.{SOURCE_LAYER_SHORT}"
    results_path = f"{username}/{PROJECT_PATH}/tasks/results"

    delete_resource(client, f"{results_path}/{TARGET_FILE_NAME}", missing_ok=True)

    attr_map, type_map = create_export_mappings_from_layer(
        client, source, log=False,
    )

    result = export_layer_to_geojson(
        client=client,
        source_layer=source,
        target_file_name=TARGET_FILE_NAME,
        target_parent_path=results_path,
        attribute_mapping=attr_map,
        attribute_type_mapping=type_map,
        log=False,
    )
    print(f"{TARGET_FILE_NAME}: {result.status}")
