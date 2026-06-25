"""Update a layer's attribute values in place via an EQL query (geoprocessing task).

The query produces the new values; rows are matched back to the target layer
by ``source_id_attribute``. Here we recompute a column on the buildings layer.
"""

import os
from evergis_tools import Client
from evergis_tools.tasks.geoprocessing import update_layer_via_eql

with Client() as client:
    username = client.account.get_user_info().username

    SAMPLE_DATA_OWNER = os.getenv("SAMPLE_DATA_OWNER", "edu")
    # Layer whose values we update in place
    target_layer = f"{SAMPLE_DATA_OWNER}.evg_overture_buildings"

    # EQL query producing the new values, keyed by the row id (gid)
    query = f"select gid, height from {target_layer}"

    update_layer_via_eql(
        eql=query,
        target_layer=target_layer,
        client=client,
        source_id_attribute="gid",
        log=True,
    )
