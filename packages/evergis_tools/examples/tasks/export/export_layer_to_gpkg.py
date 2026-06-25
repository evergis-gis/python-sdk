"""Export an EverGIS layer to a GeoPackage (.gpkg) via the importExport task.

Like the GeoJSON export, the server-side ``layer → gpkg`` handler
expects both ``attributeMapping`` and ``attributeTypeMapping`` filled
in; ``create_export_mappings_from_layer`` reads the layer schema and
builds them with identity field names + the EverGIS-native types.
"""

import os

from evergis_tools import Client, create_export_mappings_from_layer
from evergis_tools.catalog import delete_resource
from evergis_tools.tasks.export_tools import export_layer_to_gpkg


PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")

SOURCE_LAYER_SHORT = "evg_overture_buildings"
TARGET_FILE_NAME = "evg_overture_buildings.gpkg"


with Client() as client:
    username = client.account.get_user_info().username
    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    source = f"{SAMPLE_DATA_OWNER}.{SOURCE_LAYER_SHORT}"
    results_path = f"{username}/{PROJECT_PATH}/tasks/results"
    results_path = f"{username}/{PROJECT_PATH}"

    delete_resource(client, f"{results_path}/{TARGET_FILE_NAME}", missing_ok=True)

    attr_map, type_map = create_export_mappings_from_layer(
        client, source, log=False,
    )

    result = export_layer_to_gpkg(
        client=client,
        source_layer=source,
        target_file_name=TARGET_FILE_NAME,
        target_parent_path=results_path,
        target_layer_name="metro_stations",
        attribute_mapping=attr_map,
        attribute_type_mapping=type_map,
        log=True,
    )
    print(f"{TARGET_FILE_NAME}: {result.status}")
