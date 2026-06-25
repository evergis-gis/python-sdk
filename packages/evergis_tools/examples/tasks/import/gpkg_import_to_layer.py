"""Import every layer of a GPKG container into a separate EverGIS layer.

GPKG is a container: one file holds many layers. Each layer's schema
is fetched from the server and turned into ``attribute_mapping`` /
``attribute_type_mapping`` via ``build_attribute_mappings_from_schema``.

Prerequisite: the source file lives in the shared sample-data catalog
owned by ``SAMPLE_DATA_OWNER`` (default ``edu``); the import target is
created under the caller's own account.
"""

import os

from evergis_tools import Client, ResourceNotFound
from evergis_tools.catalog import add_layer_to_map
from evergis_tools.catalog.resources import resolve_resource
from evergis_tools.tasks.import_tools import (
    build_attribute_mappings_from_schema,
    get_gpkg_data_schema_rest,
    import_gpkg_to_layer,
)


client = Client()
username = client.account.get_user_info().username

PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")
SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")

SOURCE_FILE = (
    f"{SAMPLE_DATA_OWNER}/EverGIS Sample Data Catalog/Source files - raw archives"
    "/Source files - GeoPackage gpkg/natural_earth_110m.gpkg"
)
RESULTS_PATH = f"{username}/{PROJECT_PATH}/tasks/results"

# A request without layer_name returns the container's table of contents.
toc = get_gpkg_data_schema_rest(client, SOURCE_FILE)
LAYERS = [layer["name"] for layer in toc["layers"]]

for layer in LAYERS:
    schema = get_gpkg_data_schema_rest(client, SOURCE_FILE, layer_name=layer)
    attribute_mapping, attribute_type_mapping = build_attribute_mappings_from_schema(
        schema, layer_name=layer
    )

    target_layer = f"{username}.{RESOURCE_PREFIX}_gpkg_{layer}"

    # Cascade-drop the target layer if it exists - otherwise the server
    # fails with "table already exist" on re-run.
    try:
        existing = resolve_resource(client, target_layer)
        client.catalog.delete_resource(
            resourceId=existing.resourceId, cascade=True
        )
    except ResourceNotFound:
        pass

    result = import_gpkg_to_layer(
        client=client,
        source_file_name=SOURCE_FILE,
        source_layer_name=layer,
        target_layer=target_layer,
        target_layer_alias=f"gpkg import - {layer}",
        target_layer_parent_path=RESULTS_PATH,
        attribute_mapping=attribute_mapping,
        attribute_type_mapping=attribute_type_mapping,
    )
    add_layer_to_map(
        client, f"{username}.{RESOURCE_PREFIX}_map_tasks", target_layer,
    )
    print(f"{layer:>20s}: {result.status}")
