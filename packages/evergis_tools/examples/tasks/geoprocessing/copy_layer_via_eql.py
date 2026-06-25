"""Example demonstrating layer copying via EQL query using geoprocessing task.

This example shows how to copy features from one layer to another using
an EQL query, with automatic folder creation if the target path doesn't exist.
"""

import uuid
import os
from evergis_tools import Client
from evergis_tools.tasks.geoprocessing import copy_layer_via_eql

# Initialize client
client = Client()
username = client.account.get_user_info().username


SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
def short_hash(length=4):
    """Generate a short random hash for unique layer names."""
    uid = uuid.uuid4().hex  # hex characters 0-9a-f
    return uid[:length]


# System name of the target layer (schema.username.layer_name_unique_suffix)
layer_name = "places_copy"
layer_name = f"{username}.{layer_name}_{short_hash()}"

# EQL query to define which features to copy
query = f"select * from {SAMPLE_DATA_OWNER}.evg_overture_places"

# Mapping between source and target column names
columns_mapping = {
    "geometry": "geometry",
}

# Catalog path for the target layer's parent folder
# If folders don't exist, they will be created automatically
target_layer_path = f"{username}/EverGIS Resources/python/results"

print(f"Copying features to layer: {layer_name}")
print(f"Target folder path: {target_layer_path}")
print(f"Query: {query}\n")

# Run the copy task with automatic folder creation
result = copy_layer_via_eql(
    client=client,
    eql=query,
    target_layer=layer_name,
    target_layer_alias="real estate",  # Target layer alias
    target_layer_parent_path=target_layer_path,  # Auto-create folders if needed
    columns_mapping=columns_mapping,
    description="EQL copy into layer",
    log=True
)

# print("\n✓ Task completed!")
# print(f"Status: {result.status}")
# if result.error_message:
#     print(f"Error: {result.error_message}")
