"""Example: Add a layer to an existing map."""

import os
from evergis_tools.catalog import update_map

from evergis_tools import Client
client = Client()
username = client.account.get_user_info().username

SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
# Map to update
MAP_NAME = f"{username}.test_map"

layer_to_add = f"{SAMPLE_DATA_OWNER}.evg_overture_places"

# Get current map
map_info = client.projects.get_project_info(MAP_NAME)
dashboard_config = map_info.content.dashboardConfiguration

# New layer to add
new_layer = {
    "name": layer_to_add,
    "query": "",
    "opacity": 1,
    "isVisible": True,
    "parameters": {},
    "selectable": False,
    "filterZoomTo": False,
}

# Add layer to the first page
page = dashboard_config["children"][0]["children"][0]
page["layers"].append(new_layer)

# Update map
result = update_map(
    client,
    MAP_NAME,
    dashboard_configuration=dashboard_config,
)

print(f"Updated map: {result.name}")
print(f"Layers count: {len(page['layers'])}")
