
import os
from evergis_tools.tasks.network import build_isochrones

import uuid
from evergis_tools import Client
# Load environment variables from the .env file

# Initialize the client (by token)
client = Client()
username = client.account.get_extended_user_info().username

SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
# Source points layer - shared sample data (read).
table_name = f"{SAMPLE_DATA_OWNER}.evg_overture_metro_stations"
limit = "limit 1000"
where_condition = None

# Target layer - created in the caller's own catalog (write).
target_layer_name = f"{username}.metro_isochrones_{uuid.uuid4().hex[:4]}"
target_layer_alias = target_layer_name
target_layer_parent_id="efb02c4d89144f9792a94af22831f45d" # Folder ID for the target layer

# Reachability zone parameters

# EQL query selecting features to process
# query = f"SELECT * FROM {SAMPLE_DATA_OWNER}.evg_overture_places limit 1000"
query = f"SELECT * FROM {table_name} {where_condition} {limit}"
query = f"SELECT * FROM {table_name} {limit}"


build_isochrones(
    client=client,
    # provider_name="twogis_walk",
    # provider_name="sproute_isochrone_car_out",
    provider_name="sproute_isochrone_pedestrian",
    source_layer_eql=query,
    source_id_attribute="gid",
    source_geometry_attribute="geom",
    target_layer=target_layer_name,
    target_layer_alias=target_layer_alias,
    target_layer_parent_id=target_layer_parent_id,
    duration_expression="15",
    id_attribute_name="gid",
    geometry_attribute_name="geometry",
    duration_attribute_name="duration",
    base_object_id_attribute_name="object_id",
    route_center_x_attribute_name="route_center_x",
    route_center_y_attribute_name="route_center_y",
    log=True
)