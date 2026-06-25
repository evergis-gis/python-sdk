
from evergis_tools.tasks.geoprocessing import delete_from_layer_via_eql

from evergis_tools import Client

# Initialize the client (by token)
client = Client()
username = client.account.get_user_info().username

# Layer system name (schema.username.layer_name_unique_suffix)
layer_name = "places_copy"
layer_name = f"{username}.{layer_name}"

# EQL query that selects features to delete
query = f"SELECT gid FROM {layer_name} WHERE confidence < 0.5"

# Run the task that deletes features from the layer by an EQL query
delete_from_layer_via_eql(
    eql=query,
    target_layer=layer_name,
    client=client
)
