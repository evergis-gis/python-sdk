"""Import two Shapefiles into a single EverGIS layer (append pattern).

Pattern: the first task creates the target layer; the second targets
the same layer, so the server appends features instead of recreating.
The attribute schema is fetched once from the first file and reused
for the second - safe only when both sources share the same columns
and types. With diverging structures the second task would need its
own ``attribute_mapping`` / ``attribute_type_mapping``.

Prerequisite: both archives live in the shared sample-data catalog
owned by ``SAMPLE_DATA_OWNER`` (default ``edu``); the import target is
created under the caller's own account.
"""

import os

from evergis_tools import Client, ResourceNotFound
from evergis_tools.catalog import add_layer_to_map
from evergis_tools.catalog.resources import resolve_resource
from evergis_tools.tasks.import_tools import (
    build_attribute_mappings_from_schema,
    get_shapefile_data_schema_rest,
    import_shapefile_to_layer,
)


client = Client()
username = client.account.get_user_info().username

PROJECT_PATH = os.getenv("PROJECT_PATH", "EverGIS Resources/python").rstrip("/")
RESOURCE_PREFIX = os.getenv("RESOURCE_PREFIX", "evg")
SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")

SHP_DIR = (
    f"{SAMPLE_DATA_OWNER}/EverGIS Sample Data Catalog/Source files - raw archives"
    "/Source files - Shapefile"
)
SOURCE_DE = f"{SHP_DIR}/german_lands.zip"
SOURCE_IT = f"{SHP_DIR}/italian_regions.zip"
RESULTS_PATH = f"{username}/{PROJECT_PATH}/tasks/results"

TARGET_LAYER = f"{username}.{RESOURCE_PREFIX}_shp_regions"
TARGET_LAYER_ALIAS = "shp import - regions"


# Derive attribute mappings once from the first file's server schema.
schema_de = get_shapefile_data_schema_rest(client, SOURCE_DE)
attribute_mapping, attribute_type_mapping = build_attribute_mappings_from_schema(
    schema_de
)
print(f"derived attributes: {list(attribute_mapping.keys())}")

# Cascade-drop the target layer if it exists - otherwise the server fails
# with "table already exist" on re-run.
try:
    existing = resolve_resource(client, TARGET_LAYER)
    client.catalog.delete_resource(resourceId=existing.resourceId, cascade=True)
    print(f"dropped existing {TARGET_LAYER}")
except ResourceNotFound:
    pass

# Task A: creates the target layer.
result_de = import_shapefile_to_layer(
    client=client,
    source_file_name=SOURCE_DE,
    source_layer_name="german_lands",  # .shp basename inside the zip
    target_layer=TARGET_LAYER,
    target_layer_alias=TARGET_LAYER_ALIAS,
    target_layer_parent_path=RESULTS_PATH,
    attribute_mapping=attribute_mapping,
    attribute_type_mapping=attribute_type_mapping,
)
print(f"task A (DE): {result_de.status}")

# Task B: layer already exists - the server appends features rather than
# recreating. Reusing attribute_mapping works because columns match.
result_it = import_shapefile_to_layer(
    client=client,
    source_file_name=SOURCE_IT,
    source_layer_name="italian_regions",
    target_layer=TARGET_LAYER,
    target_layer_alias=TARGET_LAYER_ALIAS,
    target_layer_parent_path=RESULTS_PATH,
    attribute_mapping=attribute_mapping,
    attribute_type_mapping=attribute_type_mapping,
)
add_layer_to_map(
    client, f"{username}.{RESOURCE_PREFIX}_map_tasks", TARGET_LAYER,
)
print(f"task B (IT, append): {result_it.status}")
