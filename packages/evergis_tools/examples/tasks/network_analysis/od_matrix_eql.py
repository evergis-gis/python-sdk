
import os
from evergis_tools.tasks.network import build_od_matrix

import uuid
from evergis_tools import Client

# Initialize the client
client = Client()
username = client.account.get_extended_user_info().username


SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
# Origin features the matrix is built from
layer_from = f"{SAMPLE_DATA_OWNER}.evg_overture_districts"
source_eql = f"select * from {layer_from}"


# Destination features the matrix is built to
layer_to = f"{SAMPLE_DATA_OWNER}.evg_overture_metro_stations"
target_eql = f"select * from {layer_to}"

target_part = f"odmatrix_{uuid.uuid4().hex[:4]}"
target_layer_name = f"{username}.{target_part}"
target_layer_alias = target_layer_name

# Travel mode: "pedestrian" or "car"
transport_type = "pedestrian"


# Default values and attribute types for the result
default_values = {
    "add_text": "Calculation",
}
attribute_type_mapping = {
    "add_text": "String",
}

build_od_matrix(
    client=client,
    source_from_layer_eql=source_eql,
    source_to_layer_eql=target_eql,
    source_from_geometry_attribute="geom",
    target_layer=target_layer_name,
    target_layer_alias=target_layer_alias,
    source_to_geometry_attribute="geom",
    transport_type=transport_type,
    id_attribute_name="gid",
    id_from_attribute_name="from",
    id_to_attribute_name="to",
    transport_type_attribute_name="transport_type",
    weight_parameter_attribute_name="weight_parameter",
    distance_attribute_name="distance",
    default_values=default_values,
    attribute_type_mapping=attribute_type_mapping,
    log=True,
)
