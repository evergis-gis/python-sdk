"""Example of validating geometries using validate_layer_geometry function.

This example demonstrates:
1. Validating all geometries in a layer
2. Validating geometries filtered by EQL query
3. Using custom column names for validation results
"""

from __future__ import annotations

import os
import uuid
from evergis_tools import Client
from evergis_tools.tasks.geoprocessing import validate_layer_geometry

# Initialize client (using token)
client = Client()
username = client.account.get_user_info().username
SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")


def short_hash(length=4):
    """Generate short unique hash for layer names."""
    uid = uuid.uuid4().hex  # only characters 0-9a-f
    return uid[:length]


def example_validate_full_layer():
    """Example 1: Validate all geometries in a layer."""
    print("\n=== Example 1: Validate all geometries in a layer ===")

    # Source - shared sample data (read); target below is the caller's own.
    source_layer = f"{SAMPLE_DATA_OWNER}.evg_overture_districts"

    target_layer_name = f"{username}.invalid_{short_hash()}"
    target_layer_alias = f"Invalid {source_layer} Geometries"

    print(f"Validating layer: {source_layer}")
    print(f"Invalid geometries will be written to: {target_layer_name}")

    result = validate_layer_geometry(
        client=client,
        source_layer=source_layer,
        target_layer=target_layer_name,
        target_layer_alias=target_layer_alias,
        invalid_reason_column="error_message",
        base_object_id_attribute="source_gid",
        log=True
    )

    print(f"Task completed with status: {result.status}")
    if result.task_id:
        print(f"Task ID: {result.task_id}")


# def example_validate_with_eql():
#     """Example 2: Validate geometries filtered by EQL query."""
#     print("\n=== Example 2: Validate geometries using EQL filter ===")

#     # EQL query to select specific objects for validation
#     eql_query = f"SELECT * FROM {username}.realty3 WHERE area > 300"

#     # Target layer for invalid geometries
#     target_layer_name = f"{username}.invalid_large_realty_{short_hash()}"

#     print(f"Validating with EQL: {eql_query}")
#     print(f"Invalid geometries will be written to: {target_layer_name}")

#     result = validate_layer_geometry(
#         client=client,
#         source_layer=eql_query,
#         target_layer=target_layer_name,
#         target_layer_alias="Invalid Large Realty",
#         invalid_reason_column="validation_error",
#         base_object_id_attribute="original_id",
#         # Optional: specify parent folder for target layer
#         # target_layer_parent_id="your-folder-id-here",
#     )

#     print(f"Task completed with status: {result.status}")
#     if result.task_id:
#         print(f"Task ID: {result.task_id}")


# def example_validate_with_condition():
#     """Example 3: Validate layer with additional condition."""
#     print("\n=== Example 3: Validate layer with additional condition ===")

#     # Source layer
#     source_layer = f"{username}.realty3"

#     # Target layer for invalid geometries
#     target_layer_name = f"{username}.invalid_recent_realty_{short_hash()}"

#     print(f"Validating layer: {source_layer}")
#     print("With condition: price > 5000000")
#     print(f"Invalid geometries will be written to: {target_layer_name}")

#     result = validate_layer_geometry(
#         client=client,
#         source_layer=source_layer,
#         source_condition="price > 5000000",  # Additional filter
#         target_layer=target_layer_name,
#         target_layer_alias="Invalid Expensive Realty",
#         invalid_reason_column="error_description",
#         base_object_id_attribute="src_object_id",
#     )

#     print(f"Task completed with status: {result.status}")
#     if result.task_id:
#         print(f"Task ID: {result.task_id}")


# def example_validate_async():
#     """Example 4: Start validation without waiting for completion."""
#     print("\n=== Example 4: Async validation (no wait) ===")

#     source_layer = f"{username}.realty3"
#     target_layer_name = f"{username}.invalid_realty_async_{short_hash()}"

#     print(f"Starting validation of: {source_layer}")
#     print(f"Invalid geometries will be written to: {target_layer_name}")
#     print("Not waiting for completion...")

#     result = validate_layer_geometry(
#         client=client,
#         source_layer=source_layer,
#         target_layer=target_layer_name,
#         wait_for_completion=False,  # Don't wait
#     )

#     print(f"Task started with status: {result.status}")
#     if result.task_id:
#         print(f"Task ID: {result.task_id}")
#         print("You can check the status later using the task ID")


if __name__ == "__main__":
    # Run the example you want to test
    # Uncomment the example you want to run:

    example_validate_full_layer()
    # example_validate_with_eql()
    # example_validate_with_condition()
    # example_validate_async()

    print("\n=== All examples completed ===")
