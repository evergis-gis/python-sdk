"""Example demonstrating union operation via EQL query using geoprocessing task.

This example shows how to perform a union on features from a layer using
an EQL query, with automatic folder creation if the target path doesn't exist.
"""

import os
from evergis_tools import Client
from evergis_tools.tasks.geoprocessing import union_layers_via_eql

# Initialize client
client = Client()
username = client.account.get_user_info().username
SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")

# Source - shared sample data (read); target - the caller's own catalog (write).
source_layer = f"{SAMPLE_DATA_OWNER}.evg_overture_districts"
target_layer_name = f"{username}.overture_districts_union"

# EQL query that validates and converts geometries to multi-geometries
query = f"select gid, st_multi(st_makevalid(geometry)) as geometry from {source_layer}"

# Catalog path for the target layer's parent folder
# If folders don't exist, they will be created automatically
target_layer_path = f"{username}/EverGIS Resources/python/results"

print(f"Performing union on layer: {source_layer}")
print(f"Target layer: {target_layer_name}")
print(f"Target folder path: {target_layer_path}")
print(f"Query: {query}\n")

# validated_layer = f"{username}."
# result = validate_layer_geometry(
#     client=client,
#     source_layer=layer_name
#     target_layer=
# )

# Run the union task with automatic folder creation
result = union_layers_via_eql(
    client=client,
    eql=query,
    target_layer=target_layer_name,
    target_layer_alias="Union result",
    target_layer_parent_path=target_layer_path,  # Auto-create folders if needed
)

print("\n✓ Task completed!")
print(f"Status: {result.status}")
if result.error_message:
    print(f"Error: {result.error_message}")
